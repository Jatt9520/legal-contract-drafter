"""
法律合同拟写助手 — Flask 应用主入口
"""
import os
import json
from datetime import date, datetime
from flask import Flask, render_template, request, jsonify, Response, send_file
import config
from contracts.models import (
    ContractType, ContractRequest, AIContractRequest, PartyInfo,
    CONTRACT_TYPE_NAMES, CONTRACT_TYPE_DESCRIPTIONS, CONTRACT_TYPE_ICONS,
    CONTRACT_CATEGORIES
)
from contracts.template_engine import render_contract, get_contract_form_fields
from contracts.ai_generator import generate_contract, generate_contract_result
from contracts.exporter import export_contract

app = Flask(__name__,
            template_folder=os.path.join(config.BASE_DIR, "templates"),
            static_folder=os.path.join(config.BASE_DIR, "static"))


def get_contract_list():
    """获取合同类型列表（按分类）"""
    categories = []
    for cat_name, types in CONTRACT_CATEGORIES.items():
        items = []
        for ct in types:
            items.append({
                "type": ct.value,
                "name": CONTRACT_TYPE_NAMES[ct],
                "description": CONTRACT_TYPE_DESCRIPTIONS[ct],
                "icon": CONTRACT_TYPE_ICONS[ct],
            })
        categories.append({"name": cat_name, "contracts": items})
    return categories


# ============ 页面路由 ============

@app.route("/")
def index():
    """首页 — 合同类型选择"""
    categories = get_contract_list()
    return render_template("index.html", categories=categories, app_title=config.APP_TITLE)


@app.route("/contract/<contract_type>/form")
def contract_form(contract_type):
    """合同信息填写表单"""
    try:
        ct = ContractType(contract_type)
    except ValueError:
        return "无效的合同类型", 404

    fields = get_contract_form_fields(ct)
    type_name = CONTRACT_TYPE_NAMES[ct]
    description = CONTRACT_TYPE_DESCRIPTIONS[ct]
    return render_template("form.html",
                           contract_type=contract_type,
                           type_name=type_name,
                           description=description,
                           fields=fields,
                           app_title=config.APP_TITLE)


@app.route("/preview")
def preview():
    """合同预览页面"""
    return render_template("preview.html", app_title=config.APP_TITLE)


@app.route("/settings")
def settings_page():
    """设置页面"""
    user_config = config.load_user_config()
    return render_template("settings.html",
                           user_config=user_config,
                           app_title=config.APP_TITLE)


# ============ API 路由 ============

@app.route("/api/contracts")
def api_contracts():
    """获取合同类型列表"""
    return jsonify(get_contract_list())


@app.route("/api/contract/<contract_type>/fields")
def api_contract_fields(contract_type):
    """获取合同类型的表单字段"""
    try:
        ct = ContractType(contract_type)
    except ValueError:
        return jsonify({"error": "无效的合同类型"}), 404
    fields = get_contract_form_fields(ct)
    return jsonify({"fields": fields, "type_name": CONTRACT_TYPE_NAMES[ct]})


@app.route("/api/contract/generate", methods=["POST"])
def api_generate_contract():
    """生成合同（模板模式）"""
    data = request.json

    contract_type = data.get("contract_type")
    try:
        ct = ContractType(contract_type)
    except (ValueError, TypeError):
        return jsonify({"error": "无效的合同类型"}), 400

    # 构建当事人信息
    party_a = PartyInfo(
        name=data.get("party_a_name", ""),
        id_number=data.get("party_a_id"),
        address=data.get("party_a_address"),
        phone=data.get("party_a_phone"),
        representative=data.get("party_a_representative"),
    )
    party_b = PartyInfo(
        name=data.get("party_b_name", ""),
        id_number=data.get("party_b_id"),
        address=data.get("party_b_address"),
        phone=data.get("party_b_phone"),
        representative=data.get("party_b_representative"),
    )

    # 解析日期
    contract_date = None
    if data.get("contract_date"):
        try:
            contract_date = date.fromisoformat(data["contract_date"])
        except (ValueError, TypeError):
            pass

    # 提取自定义字段（排除通用字段）
    common_keys = {
        "contract_type", "party_a_name", "party_a_id", "party_a_address",
        "party_a_phone", "party_a_representative", "party_b_name", "party_b_id",
        "party_b_address", "party_b_phone", "party_b_representative",
        "contract_date", "contract_place", "additional_terms"
    }
    custom_fields = {k: v for k, v in data.items() if k not in common_keys}

    request_obj = ContractRequest(
        contract_type=ct,
        party_a=party_a,
        party_b=party_b,
        contract_date=contract_date,
        contract_place=data.get("contract_place"),
        custom_fields=custom_fields,
        additional_terms=data.get("additional_terms"),
    )

    result = render_contract(request_obj)
    return jsonify({
        "title": result.title,
        "content": result.content,
        "contract_type": result.contract_type,
        "mode": "template",
    })


@app.route("/api/contract/ai-generate", methods=["POST"])
def api_ai_generate():
    """AI 流式生成合同"""
    data = request.json

    contract_type = data.get("contract_type")
    ct = None
    if contract_type:
        try:
            ct = ContractType(contract_type)
        except ValueError:
            pass

    request_obj = AIContractRequest(
        contract_type=ct,
        description=data.get("description", ""),
        party_a_name=data.get("party_a_name"),
        party_b_name=data.get("party_b_name"),
        key_terms=data.get("key_terms", []),
        language=data.get("language", "zh"),
    )

    def generate():
        try:
            generator = generate_contract(request_obj, stream=True)
            collected = []
            for chunk in generator:
                collected.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            full_content = "".join(collected)
            type_name = CONTRACT_TYPE_NAMES.get(ct, "自定义合同") if ct else "自定义合同"
            yield f"data: {json.dumps({'done': True, 'title': f'{type_name}（AI 生成）', 'content': full_content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/contract/export", methods=["POST"])
def api_export():
    """导出合同"""
    data = request.json
    content = data.get("content", "")
    title = data.get("title", "合同")
    format_type = data.get("format", "pdf")

    try:
        file_path = export_contract(content, title, format_type)
        return jsonify({"file_path": file_path, "filename": os.path.basename(file_path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<path:filename>")
def api_download(filename):
    """下载导出的文件"""
    file_path = os.path.join(config.EXPORTS_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "文件不存在"}), 404


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """获取/保存设置"""
    if request.method == "GET":
        user_cfg = config.load_user_config()
        # 隐藏 API Key 的完整值
        for key in ["openai_api_key", "anthropic_api_key"]:
            if user_cfg.get(key):
                val = user_cfg[key]
                user_cfg[key] = val[:8] + "..." + val[-4:] if len(val) > 12 else "***"
        return jsonify(user_cfg)
    else:
        data = request.json
        current = config.load_user_config()
        # 如果 API Key 值包含 "..."，说明是脱敏的，不更新
        for key in ["openai_api_key", "anthropic_api_key"]:
            if key in data and ("..." in data[key] or data[key] == "***"):
                data.pop(key)
        current.update(data)
        config.save_user_config(current)
        return jsonify({"status": "ok"})


# ============ 启动 ============

def start_app(use_webview=True):
    """启动应用"""
    os.makedirs(config.EXPORTS_DIR, exist_ok=True)

    if use_webview:
        try:
            import webview
            window = webview.create_window(
                config.APP_TITLE,
                app,
                width=config.APP_WIDTH,
                height=config.APP_HEIGHT,
                min_size=(800, 600),
            )
            webview.start(debug=False)
        except ImportError:
            print("pywebview 未安装，使用浏览器模式启动...")
            import webbrowser
            webbrowser.open("http://127.0.0.1:5000")
            app.run(host="127.0.0.1", port=5000, debug=False)
    else:
        import webbrowser
        webbrowser.open("http://127.0.0.1:5000")
        app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    start_app(use_webview=True)
