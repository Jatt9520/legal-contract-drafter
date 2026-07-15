"""
法律合同拟写软件 — AI 合同生成器
支持 OpenAI 和 Anthropic Claude API
"""
import json
from typing import Generator, Optional
from contracts.models import (
    AIContractRequest, ContractResult, ContractType,
    CONTRACT_TYPE_NAMES
)
import config


SYSTEM_PROMPT = """你是一位专业的中国法律顾问和合同起草专家。你的任务是根据用户的需求，生成专业、完整、合规的合同文本。

要求：
1. 合同格式规范，包含完整的条款结构
2. 使用中国法律术语和表述习惯
3. 条款清晰明确，避免歧义
4. 包含必要的法律声明和免责条款
5. 注意保护双方合法权益的平衡
6. 输出格式为 HTML，使用适当的标题、段落和列表标签

合同结构应包含：
- 合同标题
- 合同各方信息
- 正文条款（定义、权利义务、付款、违约、争议解决等）
- 签署栏

请以纯 HTML 格式输出合同内容，不要包含 <html>、<head>、<body> 等外层标签。
使用 class 属性标记各部分，如 class="contract-title"、class="article" 等。"""


def generate_with_openai(request: AIContractRequest, stream: bool = True) -> Generator[str, None, str]:
    """使用 OpenAI API 生成合同"""
    from openai import OpenAI

    ai_config = config.get_ai_config()
    api_key = ai_config["openai_api_key"]
    model = ai_config["openai_model"]

    if not api_key:
        raise ValueError("未配置 OpenAI API Key，请在设置中配置")

    client = OpenAI(api_key=api_key)

    user_prompt = _build_user_prompt(request)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    if stream:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.3,
            max_tokens=8000,
        )
        collected = []
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                collected.append(content)
                yield content
        return "".join(collected)
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=8000,
        )
        return response.choices[0].message.content


def generate_with_anthropic(request: AIContractRequest, stream: bool = True) -> Generator[str, None, str]:
    """使用 Anthropic Claude API 生成合同"""
    from anthropic import Anthropic

    ai_config = config.get_ai_config()
    api_key = ai_config["anthropic_api_key"]
    model = ai_config["anthropic_model"]

    if not api_key:
        raise ValueError("未配置 Anthropic API Key，请在设置中配置")

    client = Anthropic(api_key=api_key)

    user_prompt = _build_user_prompt(request)

    if stream:
        with client.messages.stream(
            model=model,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.3,
        ) as stream_response:
            collected = []
            for text in stream_response.text_stream:
                collected.append(text)
                yield text
        return "".join(collected)
    else:
        response = client.messages.create(
            model=model,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.3,
        )
        return response.content[0].text


def generate_contract(request: AIContractRequest, stream: bool = True):
    """根据配置选择 AI 服务生成合同"""
    ai_config = config.get_ai_config()
    provider = ai_config["provider"]

    if provider == "anthropic":
        return generate_with_anthropic(request, stream=stream)
    else:
        return generate_with_openai(request, stream=stream)


def _build_user_prompt(request: AIContractRequest) -> str:
    """构建用户提示词"""
    parts = []

    # 合同类型
    if request.contract_type:
        type_name = CONTRACT_TYPE_NAMES.get(request.contract_type, "合同")
        parts.append(f"请生成一份【{type_name}】。")
    else:
        parts.append("请根据以下描述生成一份合同。")

    # 合同描述
    parts.append(f"\n需求描述：{request.description}")

    # 当事人信息
    if request.party_a_name:
        parts.append(f"甲方：{request.party_a_name}")
    if request.party_b_name:
        parts.append(f"乙方：{request.party_b_name}")

    # 关键条款
    if request.key_terms:
        terms_text = "、".join(request.key_terms)
        parts.append(f"\n关键条款要点：{terms_text}")

    # 语言
    if request.language == "en":
        parts.append("\n请使用英文生成合同。")
    else:
        parts.append("\n请使用中文生成合同。")

    parts.append("\n请生成完整、专业的合同文本（HTML 格式）。")

    return "\n".join(parts)


def generate_contract_result(request: AIContractRequest) -> ContractResult:
    """生成完整的合同结果对象（非流式）"""
    ai_config = config.get_ai_config()
    provider = ai_config["provider"]

    if provider == "anthropic":
        content = generate_with_anthropic(request, stream=False)
    else:
        content = generate_with_openai(request, stream=False)

    type_name = CONTRACT_TYPE_NAMES.get(request.contract_type, "合同") if request.contract_type else "自定义合同"

    return ContractResult(
        contract_type=request.contract_type.value if request.contract_type else "custom",
        title=f"{type_name}（AI 生成）",
        content=content,
        generated_at="",
        mode="ai",
    )
