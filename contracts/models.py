"""
法律合同拟写软件 — 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum


class ContractType(str, Enum):
    """合同类型枚举"""
    SALE = "sale"
    RENTAL = "rental"
    LABOR = "labor"
    SERVICE = "service"
    NDA = "nda"
    LOAN = "loan"
    PARTNERSHIP = "partnership"
    SOFTWARE_DEV = "software_dev"
    SAAS = "saas"
    AGENCY = "agency"
    CONSULTING = "consulting"
    GUARANTEE = "guarantee"
    NON_COMPETE = "non_compete"
    GIFT = "gift"
    JOINT_VENTURE = "joint_venture"


# 合同类型中文名称映射
CONTRACT_TYPE_NAMES = {
    ContractType.SALE: "买卖合同",
    ContractType.RENTAL: "租赁合同",
    ContractType.LABOR: "劳动合同",
    ContractType.SERVICE: "服务合同",
    ContractType.NDA: "保密协议（NDA）",
    ContractType.LOAN: "民间借贷合同",
    ContractType.PARTNERSHIP: "合伙协议",
    ContractType.SOFTWARE_DEV: "软件开发合同",
    ContractType.SAAS: "SaaS 服务协议",
    ContractType.AGENCY: "委托代理合同",
    ContractType.CONSULTING: "技术咨询合同",
    ContractType.GUARANTEE: "担保合同",
    ContractType.NON_COMPETE: "竞业限制协议",
    ContractType.GIFT: "赠与合同",
    ContractType.JOINT_VENTURE: "合资协议",
}

# 合同类型描述
CONTRACT_TYPE_DESCRIPTIONS = {
    ContractType.SALE: "适用于商品买卖交易，明确买卖双方的权利义务、价款、交付方式等",
    ContractType.RENTAL: "适用于房屋、设备等租赁关系，明确租赁期限、租金、维修责任等",
    ContractType.LABOR: "适用于用人单位与劳动者之间的劳动关系，明确工作内容、薪酬、福利等",
    ContractType.SERVICE: "适用于各类服务提供关系，明确服务内容、标准、费用等",
    ContractType.NDA: "适用于需要保护商业秘密和机密信息的场合",
    ContractType.LOAN: "适用于自然人之间的借贷关系，明确借款金额、利率、还款方式等",
    ContractType.PARTNERSHIP: "适用于合伙人之间的合作关系，明确出资比例、利润分配、管理职责等",
    ContractType.SOFTWARE_DEV: "适用于软件定制开发项目，明确需求、交付物、验收标准等",
    ContractType.SAAS: "适用于软件即服务订阅模式，明确服务内容、SLA、数据安全等",
    ContractType.AGENCY: "适用于委托代理关系，明确代理权限、报酬、责任等",
    ContractType.CONSULTING: "适用于技术咨询服务，明确咨询范围、成果交付、费用等",
    ContractType.GUARANTEE: "适用于担保关系，明确担保方式、范围、期限等",
    ContractType.NON_COMPETE: "适用于限制竞争行为，明确限制范围、期限、补偿等",
    ContractType.GIFT: "适用于无偿赠与关系，明确赠与物、交付方式等",
    ContractType.JOINT_VENTURE: "适用于合资合作关系，明确出资、管理、利润分配等",
}

# 合同类型图标
CONTRACT_TYPE_ICONS = {
    ContractType.SALE: "🛒",
    ContractType.RENTAL: "🏠",
    ContractType.LABOR: "👔",
    ContractType.SERVICE: "🤝",
    ContractType.NDA: "🔒",
    ContractType.LOAN: "💰",
    ContractType.PARTNERSHIP: "🤝",
    ContractType.SOFTWARE_DEV: "💻",
    ContractType.SAAS: "☁️",
    ContractType.AGENCY: "📋",
    ContractType.CONSULTING: "💡",
    ContractType.GUARANTEE: "🛡️",
    ContractType.NON_COMPETE: "⚖️",
    ContractType.GIFT: "🎁",
    ContractType.JOINT_VENTURE: "🏗️",
}

# 合同类型分类
CONTRACT_CATEGORIES = {
    "商业类": [ContractType.SALE, ContractType.RENTAL, ContractType.SERVICE],
    "劳动类": [ContractType.LABOR, ContractType.NON_COMPETE],
    "技术类": [ContractType.SOFTWARE_DEV, ContractType.SAAS, ContractType.CONSULTING],
    "金融类": [ContractType.LOAN, ContractType.GUARANTEE],
    "合作类": [ContractType.PARTNERSHIP, ContractType.JOINT_VENTURE],
    "保护类": [ContractType.NDA],
    "其他类": [ContractType.AGENCY, ContractType.GIFT],
}


class PartyInfo(BaseModel):
    """合同当事人信息"""
    name: str = Field(..., description="名称（公司名或个人姓名）")
    id_number: Optional[str] = Field(None, description="身份证号/统一社会信用代码")
    address: Optional[str] = Field(None, description="地址")
    phone: Optional[str] = Field(None, description="联系电话")
    representative: Optional[str] = Field(None, description="法定代表人/授权代表")
    email: Optional[str] = Field(None, description="电子邮箱")


class ContractRequest(BaseModel):
    """合同生成请求"""
    contract_type: ContractType = Field(..., description="合同类型")
    party_a: PartyInfo = Field(..., description="甲方信息")
    party_b: PartyInfo = Field(..., description="乙方信息")
    contract_date: Optional[date] = Field(None, description="合同签订日期")
    contract_place: Optional[str] = Field(None, description="合同签订地点")
    custom_fields: Optional[dict] = Field(default_factory=dict, description="自定义字段")
    additional_terms: Optional[str] = Field(None, description="补充条款")
    generate_mode: str = Field("template", description="生成模式: template 或 ai")
    ai_description: Optional[str] = Field(None, description="AI 模式下的合同描述")


class AIContractRequest(BaseModel):
    """AI 合同生成请求"""
    contract_type: Optional[ContractType] = Field(None, description="合同类型（可选）")
    description: str = Field(..., description="合同需求描述")
    party_a_name: Optional[str] = Field(None, description="甲方名称")
    party_b_name: Optional[str] = Field(None, description="乙方名称")
    key_terms: Optional[list[str]] = Field(default_factory=list, description="关键条款要点")
    language: str = Field("zh", description="语言: zh 中文, en 英文")


class ContractResult(BaseModel):
    """合同生成结果"""
    contract_type: str
    title: str
    content: str  # HTML 格式的合同内容
    generated_at: str
    mode: str  # "template" 或 "ai"
