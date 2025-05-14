import os, json, re, io, textwrap, traceback, contextlib
from pathlib import Path

import openai, pandas as pd, matplotlib.pyplot as plt
from dotenv import load_dotenv
from agent.prompt.prompt import SYSTEM_PROMPT, FEW_SHOT_SAMPLE, build_user_prompt
from agent.model.openai_api import OpenAIClient

# ------------------ util: sandbox executor ------------------ #
class PythonExecutor:
    """Run user-generated code in a trimmed global scope; return stdout preview."""
    def __init__(self, workdir="tmp_exec"):
        self.workdir = Path(workdir); self.workdir.mkdir(exist_ok=True)

    def run(self, code: str) -> str:
        buf, g = io.StringIO(), {
            "pd": pd,
            "plt": plt,
            "__name__": "__main__",
            "__file__": None
        }
        with contextlib.redirect_stdout(buf):
            try:
                exec(code, g)
            except Exception:
                traceback.print_exc()
        return textwrap.shorten(buf.getvalue(), 400)

# ------------------ core InsightAgent ------------------ #
class InsightAgent:
    def __init__(self,
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.0,
                 max_tool_calls: int = 3):
        load_dotenv()
        self.exec = PythonExecutor()
        self.llm = OpenAIClient(model=model, temperature=temperature)
        self.temperature = temperature
        self.max_calls = max_tool_calls

        self.system_prompt = SYSTEM_PROMPT

        # few-shots → 对话片段
        self.few_shots = []
        few_shot_tem= FEW_SHOT_SAMPLE
        for fs in few_shot_tem:
            self.few_shots.append(
                {"role": "user", "content": json.dumps(fs["input"])}
            )
            # 把 thought/code/obs 线性化
            shot_text = (f"Thought: {fs['assistant']['Thought']}\n"
                            f"```python\n{fs['assistant']['Code']}\n```\n"
                            f"Observation: {fs['assistant']['Observation']}\n"
                            f"Final Answer: {json.dumps(fs['assistant']['Final'])}")
            self.few_shots.append({"role": "assistant", "content": shot_text})

    # ---- OpenAI wrapper
    def _chat(self, messages):
        return self.llm.chat(messages)
    import json, re

    def extract_final_json(self, text) :
        """
        Robustly extract the first JSON object in `text`.

        1. 如果存在 ```json ... ``` 代码块 → 取块内内容
        2. 否则定位第一个 '{' 与最后一个 '}' → 截取
        3. 若仍失败则抛出 ValueError
        """
        # --- ① 先找 ```json ... ``` ---
        json_block = re.search(r"```json\s*({[\s\S]*?})\s*```", text, re.I)
        if json_block:
            return json.loads(json_block.group(1))

        # ---------- ② 回退：自右向左寻找成对的大括号 ---------- #
        # 只扫描 ASCII 范围，避免中文全角括号干扰
        stack, start = 0, None
        for i in range(len(text) - 1, -1, -1):
            ch = text[i]
            if ch == "}":
                if stack == 0:
                    end = i + 1             # 右边界（含）
                stack += 1
            elif ch == "{":
                stack -= 1
                if stack == 0:
                    start = i
                    candidate = text[start:end]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # 继续向前找下一对
                        pass

        raise ValueError("No valid JSON object found in assistant output.")

    # ---- 主入口：跑单一样本
    def run_sample(self, sample: dict) -> dict:
        sys_msg = {"role": "system", "content": self.system_prompt}
        user_msg = {"role": "user", "content": json.dumps({
            "question": sample["question"],
            "data_path": sample["data_file"],
            "analysis_type": sample["analysis_type"]
        })}
        conversation = [sys_msg] + self.few_shots + [user_msg]

        tool_calls = 0
        while True:
            assistant_out = self._chat(conversation)
            conversation.append({"role": "assistant", "content": assistant_out})
            print(f"Assistant: {assistant_out}")

            # ---- 抓 python 代码块
            match = re.search(r"```python(.*?)```", assistant_out, re.S)
            if match and tool_calls < self.max_calls:
                code = match.group(1).strip()
                obs  = self.exec.run(code)
                tool_calls += 1
                conversation.append(
                    {"role": "user", "content": f"Observation:\n{obs}"}
                )
                continue

            # ---- 抓 Final Answer JSON
            if "Final Answer:" in assistant_out:
                try:
                    final_json = self.extract_final_json(assistant_out)
                    # assistant_out.split("Final Answer:", 1)[1].strip().strip('\n').strip()
                    return conversation, json.loads(final_json)
                except Exception as e:
                    return conversation, assistant_out
                    # raise ValueError(f"Cannot parse JSON: {e}\n{assistant_out}")
            # 如果没匹配到，直接返回全文
            return conversation, {"raw_output": assistant_out}