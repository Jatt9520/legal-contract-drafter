"""
法律合同拟写软件 — 配置文件
"""
import os
import json

# 应用基本配置
APP_TITLE = "法律合同拟写助手"
APP_VERSION = "1.0.0"
APP_WIDTH = 1200
APP_HEIGHT = 800

# 文件路径（支持环境变量覆盖，用于便携版打包）
BASE_DIR = os.environ.get('APP_BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
CONTRACT_TEMPLATES_DIR = os.environ.get('CONTRACT_TEMPLATES_DIR', os.path.join(BASE_DIR, "contract_templates"))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")

# AI 服务配置
DEFAULT_AI_PROVIDER = "openai"  # "openai" 或 "anthropic"
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-4o"
ANTHROPIC_API_KEY = ""
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# 导出配置
DEFAULT_EXPORT_FORMAT = "pdf"  # "pdf" 或 "docx"
PDF_PAGE_SIZE = "A4"
FONT_NAME = "SimSun"  # 宋体

# 默认合同方信息
DEFAULT_PARTY_A = ""  # 甲方默认名称
DEFAULT_PARTY_B = ""  # 乙方默认名称


def load_user_config():
    """加载用户配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_user_config(config_data):
    """保存用户配置"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)


def get_ai_config():
    """获取 AI 配置（合并默认值和用户配置）"""
    user_cfg = load_user_config()
    return {
        "provider": user_cfg.get("ai_provider", DEFAULT_AI_PROVIDER),
        "openai_api_key": user_cfg.get("openai_api_key", OPENAI_API_KEY),
        "openai_model": user_cfg.get("openai_model", OPENAI_MODEL),
        "anthropic_api_key": user_cfg.get("anthropic_api_key", ANTHROPIC_API_KEY),
        "anthropic_model": user_cfg.get("anthropic_model", ANTHROPIC_MODEL),
    }
