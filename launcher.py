"""
法律合同拟写助手 — 便携版启动器
自动打开浏览器，启动 Flask 服务
"""
import os
import sys
import webbrowser
import threading
import time

# 处理 PyInstaller 打包后的路径
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    # 模板和静态文件在 _internal 目录下
    RESOURCE_DIR = os.path.join(sys._MEIPASS)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

# 设置环境变量，让 Flask 找到正确的模板和静态文件路径
os.environ['FLASK_TEMPLATE_DIR'] = os.path.join(RESOURCE_DIR, 'templates')
os.environ['FLASK_STATIC_DIR'] = os.path.join(RESOURCE_DIR, 'static')
os.environ['CONTRACT_TEMPLATES_DIR'] = os.path.join(RESOURCE_DIR, 'contract_templates')
os.environ['APP_BASE_DIR'] = BASE_DIR

# 导入 Flask 应用
from flask import Flask, render_template, request, jsonify, Response, send_file
import json
from datetime import date

import config
from contracts.models import (
    ContractType, ContractRequest, AIContractRequest, PartyInfo,
    CONTRACT_TYPE_NAMES, CONTRACT_TYPE_DESCRIPTIONS, CONTRACT_TYPE_ICONS,
    CONTRACT_CATEGORIES
)
from contracts.template_engine import render_contract, get_contract_form_fields
from contracts.ai_generator import generate_contract, generate_contract_result
from contracts.exporter import export_contract

# 重写 config 中的路径，指向正确的位置
config.BASE_DIR = RESOURCE_DIR
config.CONTRACT_TEMPLATES_DIR = os.path.join(RESOURCE_DIR, 'contract_templates')
config.EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
config.CONFIG_FILE = os.path.join(BASE_DIR, 'user_config.json')

app = Flask(__name__,
            template_folder=os.path.join(RESOURCE_DIR, 'templates'),
            static_folder=os.path.join(RESOURCE_DIR, 'static'))


def get_contract_list():
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


@app.route("/")
def index():
    categories = get_contract_list()
    return render_template("index.html", categories=categories, app_title=config.APP_TITLE)


@app.route("/contract/<contract_type>/form")
def contract_form(contract_type):
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
    return render_template("preview.html", app_title=config.APP_TITLE)


@app.route("/settings")
def settings_page():
    user_config = config.load_user_config()
    return render_template("settings.html",
                           user_config=user_config,
                           app_title=config.APP_TITLE)


@app.route("/api/contracts")
def api_contracts():
    return jsonify(get_contract_list())


@app.route("/api/contract/<contract_type>/fields")
def api_contract_fields(contract_type):
    try:
        ct = ContractType(contract_type)
    except ValueError:
        return jsonify({"error": "无效的合同类型"}), 404
    fields = get_contract_form_fields(ct)
    return jsonify({"fields": fields, "type_name": CONTRACT_TYPE_NAMES[ct]})


@app.route("/api/contract/generate", methods=["POST"])
def api_generate_contract():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        contract_type = data.get("contract_type")
        try:
            ct = ContractType(contract_type)
        except (ValueError, TypeError):
            return jsonify({"error": "无效的合同类型"}), 400

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

        contract_date = None
        if data.get("contract_date"):
            try:
                contract_date = date.fromisoformat(data["contract_date"])
            except (ValueError, TypeError):
                pass

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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/contract/ai-generate", methods=["POST"])
def api_ai_generate():
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
    try:
        data = request.json
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        content = data.get("content", "")
        title = data.get("title", "合同")
        format_type = data.get("format", "pdf")
        file_path = export_contract(content, title, format_type)
        return jsonify({"file_path": file_path, "filename": os.path.basename(file_path)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<path:filename>")
def api_download(filename):
    file_path = os.path.join(config.EXPORTS_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "文件不存在"}), 404


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        user_cfg = config.load_user_config()
        for key in ["openai_api_key", "anthropic_api_key"]:
            if user_cfg.get(key):
                val = user_cfg[key]
                user_cfg[key] = val[:8] + "..." + val[-4:] if len(val) > 12 else "***"
        return jsonify(user_cfg)
    else:
        data = request.json
        current = config.load_user_config()
        for key in ["openai_api_key", "anthropic_api_key"]:
            if key in data and ("..." in data[key] or data[key] == "***"):
                data.pop(key)
        current.update(data)
        config.save_user_config(current)
        return jsonify({"status": "ok"})


def open_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")


def main():
    os.makedirs(config.EXPORTS_DIR, exist_ok=True)
    print("=" * 50)
    print("  法律合同拟写助手 v1.0")
    print("  正在启动，请稍候...")
    print("=" * 50)

    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    # 启动 Flask
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
