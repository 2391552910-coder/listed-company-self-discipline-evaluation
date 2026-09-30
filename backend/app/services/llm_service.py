"""
大模型调用服务（论文 4.3.1：大模型 API 调用流程）

基于 LangChain 调用 DeepSeek（OpenAI 兼容接口），支持结构化 JSON 输出解析。
"""
import json
import re
from functools import lru_cache

from langchain_core.prompts import PromptTemplate

from app.config import settings
from app.core.exceptions import BusinessException
from app.rag.prompts import EVALUATION_PROMPT, EXTRACTION_PROMPT, SUMMARY_PROMPT


@lru_cache(maxsize=1)
def get_llm():
    """懒加载并缓存大模型客户端"""
    from langchain_openai import ChatOpenAI

    if not settings.LLM_API_KEY:
        raise BusinessException("未配置 LLM_API_KEY，请在 .env 中设置 DeepSeek API Key")
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
    )


def parse_json_output(text: str) -> dict:
    """从模型输出中稳健解析 JSON（容忍 ```json 包裹与前后缀文本）"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            text = m.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise BusinessException(f"大模型输出 JSON 解析失败: {e}; 原始输出: {text[:200]}")


class LLMService:
    """大模型服务：信息抽取、维度评价、总体摘要"""

    def extract_facts(self, dimension_name: str, context: str) -> dict:
        """按维度从年报文本抽取自律相关事实（4.2.2）"""
        prompt = PromptTemplate.from_template(EXTRACTION_PROMPT).format(
            dimension_name=dimension_name, context=context[:8000]
        )
        resp = get_llm().invoke(prompt)
        return parse_json_output(resp.content)

    def evaluate_dimension(self, stock_name: str, stock_code: str, year: int,
                           dimension_name: str, dimension_desc: str,
                           facts: str, regulations: str) -> dict:
        """生成单维度评价，注入 RAG 检索的法规依据（4.2.3 / 4.4.3）"""
        prompt = PromptTemplate.from_template(EVALUATION_PROMPT).format(
            stock_name=stock_name, stock_code=stock_code, year=year,
            dimension_name=dimension_name, dimension_desc=dimension_desc,
            facts=facts, regulations=regulations,
        )
        resp = get_llm().invoke(prompt)
        return parse_json_output(resp.content)

    def summarize(self, stock_name: str, stock_code: str, year: int,
                  evaluations: str) -> dict:
        """基于四维评价生成总体摘要"""
        prompt = PromptTemplate.from_template(SUMMARY_PROMPT).format(
            stock_name=stock_name, stock_code=stock_code, year=year, evaluations=evaluations
        )
        resp = get_llm().invoke(prompt)
        return parse_json_output(resp.content)


llm_service = LLMService()
