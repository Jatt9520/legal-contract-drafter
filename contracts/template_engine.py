"""
法律合同拟写软件 — Jinja2 模板渲染引擎
"""
import os
from datetime import date
from jinja2 import Environment, FileSystemLoader, select_autoescape
from contracts.models import (
    ContractType, ContractRequest, ContractResult,
    CONTRACT_TYPE_NAMES
)
import config


def create_jinja_env():
    """创建 Jinja2 环境"""
    templates_dir = config.CONTRACT_TEMPLATES_DIR
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # 注册自定义过滤器
    env.filters["format_date"] = format_date
    env.filters["format_amount"] = format_amount
    return env


def format_date(value, fmt="%Y年%m月%d日"):
    """格式化日期"""
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(value, date):
        return value.strftime(fmt)
    return str(value) if value else "____年__月__日"


def format_amount(value):
    """格式化金额，添加大写"""
    if not value:
        return "____元（¥0.00）"
    try:
        amount = float(value)
        cn_amount = number_to_chinese(amount)
        return f"{cn_amount}（¥{amount:,.2f}）"
    except (ValueError, TypeError):
        return str(value)


def number_to_chinese(amount):
    """数字金额转中文大写"""
    digits = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]
    units = ["", "拾", "佰", "仟"]
    big_units = ["", "万", "亿"]

    integer_part = int(amount)
    decimal_part = round((amount - integer_part) * 100)

    if integer_part == 0:
        result = "零"
    else:
        result = ""
        str_num = str(integer_part)
        length = len(str_num)
        for i, ch in enumerate(str_num):
            d = int(ch)
            pos = length - i - 1
            big_unit_idx = pos // 4
            unit_idx = pos % 4

            if d != 0:
                result += digits[d] + units[unit_idx]
            else:
                if unit_idx == 0 and big_unit_idx > 0:
                    result = result.rstrip("零")
                    result += big_units[big_unit_idx]
                elif not result.endswith("零"):
                    result += "零"
        result = result.rstrip("零")

    if decimal_part == 0:
        result += "元整"
    else:
        jiao = decimal_part // 10
        fen = decimal_part % 10
        result += "元"
        if jiao > 0:
            result += digits[jiao] + "角"
        elif fen > 0:
            result += "零"
        if fen > 0:
            result += digits[fen] + "分"

    return result


def get_template_filename(contract_type: ContractType) -> str:
    """获取合同模板文件名"""
    return f"{contract_type.value}.html"


def render_contract(request: ContractRequest) -> ContractResult:
    """渲染合同"""
    env = create_jinja_env()
    template_file = get_template_filename(request.contract_type)

    try:
        template = env.get_template(template_file)
    except Exception:
        # 如果模板不存在，使用通用模板
        template = env.get_template("_generic.html")

    # 准备模板上下文
    today = request.contract_date or date.today()
    context = {
        "party_a": request.party_a,
        "party_b": request.party_b,
        "contract_date": today,
        "contract_date_cn": format_date(today),
        "contract_place": request.contract_place or "________",
        "custom_fields": request.custom_fields or {},
        "additional_terms": request.additional_terms or "",
        "contract_type_name": CONTRACT_TYPE_NAMES.get(request.contract_type, "合同"),
    }
    # 合并自定义字段到顶层
    context.update(request.custom_fields or {})

    content = template.render(**context)
    title = f"{CONTRACT_TYPE_NAMES.get(request.contract_type, '合同')}"

    return ContractResult(
        contract_type=request.contract_type.value,
        title=title,
        content=content,
        generated_at=date.today().isoformat(),
        mode="template",
    )


def get_contract_form_fields(contract_type: ContractType) -> list[dict]:
    """获取合同类型的表单字段定义"""
    common_fields = [
        {"name": "party_a_name", "label": "甲方名称", "type": "text", "required": True,
         "placeholder": "公司名称或个人姓名"},
        {"name": "party_a_id", "label": "甲方证件号", "type": "text", "required": False,
         "placeholder": "身份证号/统一社会信用代码"},
        {"name": "party_a_address", "label": "甲方地址", "type": "text", "required": False},
        {"name": "party_a_phone", "label": "甲方电话", "type": "text", "required": False},
        {"name": "party_a_representative", "label": "甲方法定代表人", "type": "text", "required": False},
        {"name": "party_b_name", "label": "乙方名称", "type": "text", "required": True,
         "placeholder": "公司名称或个人姓名"},
        {"name": "party_b_id", "label": "乙方证件号", "type": "text", "required": False,
         "placeholder": "身份证号/统一社会信用代码"},
        {"name": "party_b_address", "label": "乙方地址", "type": "text", "required": False},
        {"name": "party_b_phone", "label": "乙方电话", "type": "text", "required": False},
        {"name": "party_b_representative", "label": "乙方法定代表人", "type": "text", "required": False},
        {"name": "contract_date", "label": "签订日期", "type": "date", "required": False},
        {"name": "contract_place", "label": "签订地点", "type": "text", "required": False},
    ]

    # 各合同类型特有的字段
    type_specific_fields = {
        ContractType.SALE: [
            {"name": "goods_name", "label": "商品名称", "type": "text", "required": True},
            {"name": "goods_spec", "label": "商品规格/型号", "type": "text", "required": False},
            {"name": "quantity", "label": "数量", "type": "text", "required": True},
            {"name": "unit_price", "label": "单价（元）", "type": "number", "required": True},
            {"name": "total_amount", "label": "总金额（元）", "type": "number", "required": True},
            {"name": "delivery_date", "label": "交付日期", "type": "date", "required": False},
            {"name": "delivery_place", "label": "交付地点", "type": "text", "required": False},
            {"name": "payment_method", "label": "付款方式", "type": "select", "required": True,
             "options": ["一次性付清", "分期付款", "货到付款", "预付定金+尾款"]},
            {"name": "warranty_period", "label": "质保期限", "type": "text", "required": False},
        ],
        ContractType.RENTAL: [
            {"name": "property_address", "label": "租赁物地址", "type": "text", "required": True},
            {"name": "property_area", "label": "面积（㎡）", "type": "number", "required": False},
            {"name": "property_usage", "label": "用途", "type": "select", "required": True,
             "options": ["住宅", "办公", "商业", "仓储", "其他"]},
            {"name": "lease_start", "label": "租赁起始日", "type": "date", "required": True},
            {"name": "lease_end", "label": "租赁终止日", "type": "date", "required": True},
            {"name": "monthly_rent", "label": "月租金（元）", "type": "number", "required": True},
            {"name": "deposit", "label": "押金（元）", "type": "number", "required": False},
            {"name": "payment_day", "label": "每月付款日", "type": "number", "required": False},
            {"name": "maintenance_responsibility", "label": "维修责任", "type": "select",
             "required": False, "options": ["出租方承担", "承租方承担", "各自承担各自部分"]},
        ],
        ContractType.LABOR: [
            {"name": "position", "label": "岗位/职位", "type": "text", "required": True},
            {"name": "department", "label": "部门", "type": "text", "required": False},
            {"name": "work_location", "label": "工作地点", "type": "text", "required": True},
            {"name": "contract_start", "label": "合同起始日", "type": "date", "required": True},
            {"name": "contract_end", "label": "合同终止日", "type": "date", "required": False},
            {"name": "probation_period", "label": "试用期", "type": "text", "required": False},
            {"name": "salary", "label": "月薪（元）", "type": "number", "required": True},
            {"name": "work_hours", "label": "工作时间", "type": "select", "required": True,
             "options": ["标准工时制", "综合计算工时制", "不定时工作制"]},
            {"name": "annual_leave", "label": "年假天数", "type": "number", "required": False},
        ],
        ContractType.SERVICE: [
            {"name": "service_content", "label": "服务内容", "type": "textarea", "required": True},
            {"name": "service_standard", "label": "服务标准", "type": "textarea", "required": False},
            {"name": "service_period_start", "label": "服务起始日", "type": "date", "required": True},
            {"name": "service_period_end", "label": "服务终止日", "type": "date", "required": True},
            {"name": "service_fee", "label": "服务费用（元）", "type": "number", "required": True},
            {"name": "payment_method", "label": "付款方式", "type": "select", "required": True,
             "options": ["一次性付清", "按月支付", "按季支付", "按阶段支付", "完成后支付"]},
        ],
        ContractType.NDA: [
            {"name": "confidential_scope", "label": "保密范围", "type": "textarea", "required": True},
            {"name": "nda_period", "label": "保密期限（年）", "type": "number", "required": True},
            {"name": "purpose", "label": "合作目的", "type": "textarea", "required": False},
            {"name": "penalty_amount", "label": "违约金（元）", "type": "number", "required": False},
        ],
        ContractType.LOAN: [
            {"name": "loan_amount", "label": "借款金额（元）", "type": "number", "required": True},
            {"name": "loan_purpose", "label": "借款用途", "type": "text", "required": False},
            {"name": "interest_rate", "label": "年利率（%）", "type": "number", "required": True},
            {"name": "loan_start", "label": "借款起始日", "type": "date", "required": True},
            {"name": "loan_end", "label": "还款日期", "type": "date", "required": True},
            {"name": "repayment_method", "label": "还款方式", "type": "select", "required": True,
             "options": ["一次性还本付息", "等额本息", "等额本金", "先息后本"]},
            {"name": "guarantee_method", "label": "担保方式", "type": "select", "required": False,
             "options": ["无担保", "抵押", "质押", "保证"]},
        ],
        ContractType.PARTNERSHIP: [
            {"name": "business_name", "label": "合伙企业名称", "type": "text", "required": True},
            {"name": "business_scope", "label": "经营范围", "type": "textarea", "required": True},
            {"name": "party_a_contribution", "label": "甲方出资额（元）", "type": "number", "required": True},
            {"name": "party_b_contribution", "label": "乙方出资额（元）", "type": "number", "required": True},
            {"name": "profit_ratio_a", "label": "甲方利润分配比例（%）", "type": "number", "required": True},
            {"name": "partnership_period", "label": "合伙期限（年）", "type": "number", "required": False},
        ],
        ContractType.SOFTWARE_DEV: [
            {"name": "project_name", "label": "项目名称", "type": "text", "required": True},
            {"name": "project_description", "label": "项目描述/需求概述", "type": "textarea", "required": True},
            {"name": "tech_stack", "label": "技术栈要求", "type": "text", "required": False},
            {"name": "dev_period", "label": "开发周期（天）", "type": "number", "required": True},
            {"name": "total_fee", "label": "开发费用（元）", "type": "number", "required": True},
            {"name": "milestones", "label": "里程碑/阶段划分", "type": "textarea", "required": False},
            {"name": "acceptance_criteria", "label": "验收标准", "type": "textarea", "required": False},
            {"name": "warranty_period", "label": "维护期（月）", "type": "number", "required": False},
            {"name": "ip_ownership", "label": "知识产权归属", "type": "select", "required": True,
             "options": ["归委托方所有", "归开发方所有", "双方共有"]},
        ],
        ContractType.SAAS: [
            {"name": "service_name", "label": "SaaS 服务名称", "type": "text", "required": True},
            {"name": "service_description", "label": "服务描述", "type": "textarea", "required": True},
            {"name": "subscription_plan", "label": "订阅方案", "type": "select", "required": True,
             "options": ["基础版", "专业版", "企业版", "定制版"]},
            {"name": "subscription_fee", "label": "订阅费用（元/年）", "type": "number", "required": True},
            {"name": "subscription_start", "label": "订阅起始日", "type": "date", "required": True},
            {"name": "subscription_end", "label": "订阅终止日", "type": "date", "required": True},
            {"name": "sla_uptime", "label": "SLA 可用性（%）", "type": "number", "required": False},
            {"name": "data_retention", "label": "数据保留期限（天）", "type": "number", "required": False},
            {"name": "user_limit", "label": "用户数限制", "type": "number", "required": False},
        ],
        ContractType.AGENCY: [
            {"name": "agency_scope", "label": "代理范围/权限", "type": "textarea", "required": True},
            {"name": "agency_area", "label": "代理区域", "type": "text", "required": False},
            {"name": "agency_period_start", "label": "代理起始日", "type": "date", "required": True},
            {"name": "agency_period_end", "label": "代理终止日", "type": "date", "required": True},
            {"name": "agency_fee", "label": "代理费用/佣金（元）", "type": "number", "required": True},
            {"name": "commission_rate", "label": "佣金比例（%）", "type": "number", "required": False},
        ],
        ContractType.CONSULTING: [
            {"name": "consulting_scope", "label": "咨询范围", "type": "textarea", "required": True},
            {"name": "deliverables", "label": "交付成果", "type": "textarea", "required": True},
            {"name": "consulting_period_start", "label": "咨询起始日", "type": "date", "required": True},
            {"name": "consulting_period_end", "label": "咨询终止日", "type": "date", "required": True},
            {"name": "consulting_fee", "label": "咨询费用（元）", "type": "number", "required": True},
        ],
        ContractType.GUARANTEE: [
            {"name": "principal_debt", "label": "主债权金额（元）", "type": "number", "required": True},
            {"name": "guarantee_type", "label": "担保方式", "type": "select", "required": True,
             "options": ["一般保证", "连带责任保证"]},
            {"name": "guarantee_scope", "label": "担保范围", "type": "textarea", "required": True},
            {"name": "guarantee_start", "label": "担保起始日", "type": "date", "required": True},
            {"name": "guarantee_end", "label": "担保终止日", "type": "date", "required": True},
        ],
        ContractType.NON_COMPETE: [
            {"name": "restriction_scope", "label": "限制范围", "type": "textarea", "required": True},
            {"name": "restriction_area", "label": "限制地域", "type": "text", "required": True},
            {"name": "restriction_period", "label": "限制期限（月）", "type": "number", "required": True},
            {"name": "compensation", "label": "经济补偿（元/月）", "type": "number", "required": True},
            {"name": "penalty", "label": "违约金（元）", "type": "number", "required": False},
        ],
        ContractType.GIFT: [
            {"name": "gift_item", "label": "赠与物", "type": "text", "required": True},
            {"name": "gift_description", "label": "赠与物描述", "type": "textarea", "required": False},
            {"name": "gift_value", "label": "赠与物价值（元）", "type": "number", "required": False},
            {"name": "delivery_date", "label": "交付日期", "type": "date", "required": False},
            {"name": "conditions", "label": "附加条件", "type": "textarea", "required": False},
        ],
        ContractType.JOINT_VENTURE: [
            {"name": "project_name", "label": "合资项目名称", "type": "text", "required": True},
            {"name": "project_description", "label": "项目描述", "type": "textarea", "required": True},
            {"name": "party_a_investment", "label": "甲方出资额（元）", "type": "number", "required": True},
            {"name": "party_b_investment", "label": "乙方出资额（元）", "type": "number", "required": True},
            {"name": "profit_ratio_a", "label": "甲方利润分配比例（%）", "type": "number", "required": True},
            {"name": "venture_period", "label": "合资期限（年）", "type": "number", "required": False},
            {"name": "management_structure", "label": "管理架构", "type": "textarea", "required": False},
        ],
    }

    fields = common_fields + type_specific_fields.get(contract_type, [])
    # 添加通用的补充条款字段
    fields.append({
        "name": "additional_terms",
        "label": "补充条款",
        "type": "textarea",
        "required": False,
        "placeholder": "如有其他约定事项，请在此补充说明",
    })
    return fields
