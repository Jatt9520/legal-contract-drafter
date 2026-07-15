# ⚖️ 法律合同拟写助手

专业的法律合同拟写工具，支持 **15 种常见合同类型**，提供模板填充和 AI 智能生成两种模式，可导出 PDF 和 Word 文档。

## ✨ 功能特点

- 📋 **模板模式** — 选择合同类型，填写表单一键生成标准合同
- 🤖 **AI 智能模式** — 描述合同需求，AI 自动生成完整合同条款（流式输出）
- 📄 **15 种合同模板** — 覆盖商业、劳动、技术、金融、合作等领域
- 📥 **导出功能** — 支持导出 PDF 和 Word (docx) 格式
- ✏️ **在线编辑** — 生成后可直接编辑合同内容
- 💻 **桌面应用** — 基于 pywebview 的原生桌面窗口体验

## 📑 支持的合同类型

| 类别 | 合同类型 |
|------|----------|
| 商业类 | 买卖合同、租赁合同、服务合同 |
| 劳动类 | 劳动合同、竞业限制协议 |
| 技术类 | 软件开发合同、SaaS 服务协议、技术咨询合同 |
| 金融类 | 民间借贷合同、担保合同 |
| 合作类 | 合伙协议、合资协议 |
| 保护类 | 保密协议 (NDA) |
| 其他类 | 委托代理合同、赠与合同 |

## 🚀 快速开始

### 方式一：源码运行（推荐）

```bash
# 克隆仓库
git clone https://github.com/Jatt9520/legal-contract-drafter.git
cd legal-contract-drafter

# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

启动后在浏览器访问 http://127.0.0.1:5000

### 方式二：自行打包便携版

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
python -m PyInstaller build.spec --noconfirm

# 便携版输出在 dist/法律合同拟写助手/ 目录
```

## ⚙️ 配置 AI 功能

启动应用后进入 **设置** 页面，配置 AI 服务：

| 服务商 | 说明 |
|--------|------|
| **OpenAI** | 需要 GPT-4o API Key，[获取地址](https://platform.openai.com/api-keys) |
| **Anthropic** | 需要 Claude API Key，[获取地址](https://console.anthropic.com/) |

配置完成后即可使用 AI 智能生成功能。

## 📁 项目结构

```
legal_contract_drafter/
├── app.py                  # Flask 应用主入口
├── launcher.py             # 便携版启动器
├── config.py               # 配置文件
├── requirements.txt        # Python 依赖
├── build.spec              # PyInstaller 打包配置
├── contracts/              # 核心逻辑模块
│   ├── models.py           # 数据模型
│   ├── template_engine.py  # Jinja2 模板引擎
│   ├── ai_generator.py     # AI 合同生成器
│   └── exporter.py         # PDF/Word 导出
├── contract_templates/     # 15 个合同模板 (Jinja2)
├── templates/              # Web 页面模板
└── static/                 # 前端资源 (CSS/JS)
```

## 🛠️ 技术栈

- **后端**: Flask + Jinja2
- **前端**: HTML + CSS + JavaScript
- **桌面**: pywebview
- **AI**: OpenAI API / Anthropic Claude API
- **导出**: weasyprint (PDF) + python-docx (Word)
- **打包**: PyInstaller

## 📦 依赖

```
flask>=3.0
pywebview>=5.0
jinja2>=3.1
openai>=1.0
anthropic>=0.30
python-docx>=1.1
weasyprint>=62.0
pydantic>=2.0
```

## ⚠️ 免责声明

- 本工具生成的合同仅供参考，**不构成法律建议**
- 签署合同前请仔细审查各项条款
- **建议咨询专业律师**以确保合同的合法性和有效性
- AI 生成的内容需要用户自行审核

## 📄 许可证

MIT License
