"""
openai_wrapper.py  —— 轻量封装 OpenAI ChatCompletion
"""

import os, time, random, logging
from typing import List, Dict

import openai
from dotenv import load_dotenv

log = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self,
                 model: str = "gpt-4o",
                 temperature: float = 0.0,
                 max_tokens: int | None = None,
                 retries: int = 4,
                 backoff: float = 2.0):
        """
        Parameters
        ----------
        model        : OpenAI model name
        temperature  : sampling temperature
        max_tokens   : None → let API decide
        retries      : 重试次数
        backoff      : 初始退避秒数（指数 *2）
        """
        load_dotenv()                          # 读取 .env
        with open("/home/BA_agent/openai.api_key", "r", encoding="utf-8") as f:
            openai.api_key = f.read().strip()
        # openai.api_key = ""
        openai.base_url = "https://api.gpt.ge/v1/"

        self.model, self.temperature = model, temperature
        self.max_tokens, self.retries, self.backoff = max_tokens, retries, backoff

        if not openai.api_key:
            raise EnvironmentError("OPENAI_API_KEY not set in .env or env vars")

    # -------- Chat Completion -------- #
    def chat(self,
             messages: List[Dict[str, str]],
             tools: list | None = None,
             **extra_kwargs) -> str:
        """
        Parameters
        ----------
        messages : [{"role":"system","content":"..."}, ...]
        tools    : optional tool spec (function calling)
        extra_kwargs : other kwargs for openai.chat.completions.create
        """
        attempt, wait = 0, self.backoff
        while True:
            try:
                resp = openai.chat.completions.create(
                    model       = self.model,
                    temperature = self.temperature,
                    max_tokens  = self.max_tokens,
                    messages    = messages,
                    tools       = tools,
                    **extra_kwargs
                )
                return resp.choices[0].message.content
            except Exception as e:
                attempt += 1
                if attempt > self.retries:
                    raise RuntimeError(f"OpenAI API fail after {self.retries} retries") from e
                jitter = random.uniform(0, 0.5)
                log.warning(f"[OpenAI retry {attempt}] {e} → sleep {wait+jitter:.1f}s")
                time.sleep(wait + jitter)
                wait *= 2