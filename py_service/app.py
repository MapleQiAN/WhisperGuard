from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
import os
from dotenv import load_dotenv
import openai
import json
import requests
import aiohttp
import asyncio

# 加载环境变量
load_dotenv()

app = FastAPI(title="WhisprGuard API", description="语义隐私助手API服务")

# 配置API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

class TextRequest(BaseModel):
    text: str
    model: Literal["openai", "deepseek", "ollama"] = "openai"  # 默认使用OpenAI
    ollama_model: str = "qwen:7b"  # 默认使用Qwen模型

class TextResponse(BaseModel):
    sensitive_words: List[str]
    risk_level: str
    risk_reason: str
    rewrite: List[str]

async def analyze_with_ollama(text: str, model: str = "qwen:7b") -> dict:
    try:
        prompt = f"""请分析以下文本在中国互联网语境下的风险等级，并提供改写建议。
文本内容：{text}

请以JSON格式返回分析结果，包含以下字段：
- sensitive_words: 发现的敏感词列表
- risk_level: 风险等级（低/中/高）
- risk_reason: 风险原因分析
- rewrite: 2-3个改写建议

注意：
1. 考虑政治、社会、文化等多方面因素
2. 分析要具体且专业
3. 改写建议要委婉但保持原意
4. 返回格式必须是合法的JSON"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                OLLAMA_API_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API请求失败: {response.status}")
                
                result = await response.json()
                try:
                    return json.loads(result["response"])
                except json.JSONDecodeError:
                    # 如果返回的不是有效的JSON，尝试提取JSON部分
                    response_text = result["response"]
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        return json.loads(response_text[json_start:json_end])
                    raise Exception("无法解析Ollama响应为JSON格式")

    except Exception as e:
        print(f"Ollama分析失败: {e}")
        raise

def analyze_with_openai(text: str) -> dict:
    try:
        prompt = f"""请分析以下文本在中国互联网语境下的风险等级，并提供改写建议。
文本内容：{text}

请以JSON格式返回分析结果，包含以下字段：
- sensitive_words: 发现的敏感词列表
- risk_level: 风险等级（低/中/高）
- risk_reason: 风险原因分析
- rewrite: 2-3个改写建议

注意：
1. 考虑政治、社会、文化等多方面因素
2. 分析要具体且专业
3. 改写建议要委婉但保持原意
4. 返回格式必须是合法的JSON"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的文本风险分析专家，擅长识别文本中的潜在风险并提供改写建议。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"OpenAI分析失败: {e}")
        raise

def analyze_with_deepseek(text: str) -> dict:
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""请分析以下文本在中国互联网语境下的风险等级，并提供改写建议。
文本内容：{text}

请以JSON格式返回分析结果，包含以下字段：
- sensitive_words: 发现的敏感词列表
- risk_level: 风险等级（低/中/高）
- risk_reason: 风险原因分析
- rewrite: 2-3个改写建议

注意：
1. 考虑政治、社会、文化等多方面因素
2. 分析要具体且专业
3. 改写建议要委婉但保持原意
4. 返回格式必须是合法的JSON"""

        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的文本风险分析专家，擅长识别文本中的潜在风险并提供改写建议。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return json.loads(result["choices"][0]["message"]["content"])

    except Exception as e:
        print(f"DeepSeek分析失败: {e}")
        raise

async def analyze_with_ai(text: str, model: str = "openai", ollama_model: str = "qwen:7b") -> dict:
    try:
        if model == "openai":
            return analyze_with_openai(text)
        elif model == "deepseek":
            return analyze_with_deepseek(text)
        elif model == "ollama":
            return await analyze_with_ollama(text, ollama_model)
        else:
            raise ValueError(f"不支持的模型: {model}")
    except Exception as e:
        print(f"AI分析失败: {e}")
        return {
            "sensitive_words": [],
            "risk_level": "未知",
            "risk_reason": f"AI分析服务暂时不可用: {str(e)}",
            "rewrite": ["请稍后重试"]
        }

@app.post("/analyze", response_model=TextResponse)
async def analyze_text(request: TextRequest):
    try:
        result = await analyze_with_ai(request.text, request.model, request.ollama_model)
        return TextResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 