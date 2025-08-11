import os, json, re, io, textwrap, traceback, contextlib
from pathlib import Path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from agent.prompt.prompt import SYSTEM_PROMPT, FEW_SHOT_SAMPLE, build_user_prompt
from agent.model.openai_api import OpenAIClient



# ------------------ Data tool: safe loader & analytics ------------------ #
class DataHub:
    """
    A minimal, sandboxed data API for the agent.
    Supports CSV/XLSX/JSON; stores DataFrames by id for later ops.
    """
    def __init__(self, root: str | Path = "."):
        self.root = Path(root)
        self._frames: dict[str, pd.DataFrame] = {}
        self._counter = 0

    # ---------- loading ----------
    def load(self, path: str, sheet: int | str | None = None) -> dict:
        """
        Load a dataset, return a small meta dict.
        Supports: .csv / .xlsx / .json
        """
        p = self._safe_path(path)
        suffix = p.suffix.lower()

        if suffix == ".csv":
            df = self._read_csv(p)
        elif suffix in (".xlsx", ".xls"):
            df = self._read_excel(p, sheet=sheet)
        elif suffix == ".json":
            df = self._read_json(p)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        df_id = self._store(df)
        meta = {
            "df_id": df_id,
            "n_rows": int(len(df)),
            "n_cols": int(df.shape[1]),
            "columns": list(map(str, df.columns)),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()}
        }
        return meta

    def _read_csv(self, path: Path) -> pd.DataFrame:
        # Try common encodings; fall back to utf-8
        encodings = ["utf-8", "utf-8-sig", "gbk", "latin1"]
        last_err = None
        for enc in encodings:
            try:
                return pd.read_csv(path, engine="python", encoding=enc, keep_default_na=True)
            except Exception as e:
                last_err = e
        raise last_err

    def _read_excel(self, path: Path, sheet=None) -> pd.DataFrame:
        if sheet is None:
            return pd.read_excel(path)
        return pd.read_excel(path, sheet_name=sheet)

    def _read_json(self, path: Path) -> pd.DataFrame:
        """
        Accepts:
        - list[dict] -> DataFrame
        - dict[str, list] / dict[str, dict] -> DataFrame
        - dict with 'data' key
        """
        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, list):
            return pd.DataFrame(obj)
        if isinstance(obj, dict):
            if "data" in obj and isinstance(obj["data"], (list, dict)):
                return pd.DataFrame(obj["data"])
            return pd.DataFrame(obj)
        raise ValueError("Unsupported JSON structure for tabular loading.")

    def _safe_path(self, path: str) -> Path:
        p = (self.root / path).resolve()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"File not found: {p}")
        # Optional: prevent escaping project root
        root = self.root.resolve()
        if root not in p.parents and p != root:
            raise PermissionError(f"Access outside of root is not allowed: {p}")
        return p

    def _store(self, df: pd.DataFrame) -> str:
        self._counter += 1
        df_id = f"df_{self._counter}"
        self._frames[df_id] = df
        return df_id

    # ---------- exploration ----------
    def head(self, df_id: str, n: int = 5) -> pd.DataFrame:
        return self._get(df_id).head(n)

    def describe(self, df_id: str) -> dict:
        df = self._get(df_id)
        na_per_col = df.isna().sum().to_dict()
        return {
            "shape": list(df.shape),
            "na_per_col": {k: int(v) for k, v in na_per_col.items()},
            "sample_rows": json.loads(df.head(3).to_json(orient="records"))
        }

    def columns(self, df_id: str) -> list[str]:
        return list(map(str, self._get(df_id).columns))

    # ---------- aggregations ----------
    def mean(self, df_id: str, col: str) -> float:
        df = self._get(df_id)
        if col not in df.columns:
            raise KeyError(f"Column not found: {col}")
        return float(pd.to_numeric(df[col], errors="coerce").mean(skipna=True))

    def groupby_nan_count(self, df_id: str, group_col: str) -> pd.DataFrame:
        """
        Count missing cells per group across ALL columns except the group column.
        """
        df = self._get(df_id)
        if group_col not in df.columns:
            raise KeyError(f"Group column not found: {group_col}")
        # Count NaN across non-group columns row-wise, then sum by group
        mask_cols = [c for c in df.columns if c != group_col]
        per_row_missing = df[mask_cols].isna().sum(axis=1)
        out = (
            pd.DataFrame({group_col: df[group_col], "_row_missing": per_row_missing})
            .groupby(group_col, dropna=False)["_row_missing"]
            .sum()
            .reset_index()
            .rename(columns={group_col: "group", "_row_missing": "num_missing"})
        )
        # normalize types
        out["group"] = out["group"].astype(str)
        out["num_missing"] = out["num_missing"].astype(int)
        return out

    def argmax_missing(self, df_id: str, group_col: str) -> dict:
        """
        Return the group with the most missing values (as counted above).
        """
        g = self.groupby_nan_count(df_id, group_col)
        if len(g) == 0:
            return {"group": None, "num_missing": 0}
        idx = int(g["num_missing"].astype(int).idxmax())
        row = g.iloc[idx]
        return {"group": str(row["group"]), "num_missing": int(row["num_missing"])}

    # ---------- utilities ----------
    def to_table(self, df_id: str, orient: str = "records", limit: int = 20) -> list[dict]:
        df = self._get(df_id).head(limit)
        return json.loads(df.to_json(orient=orient))

    def _get(self, df_id: str) -> pd.DataFrame:
        if df_id not in self._frames:
            raise KeyError(f"Unknown df_id: {df_id}")
        return self._frames[df_id]


# ------------------ util: sandbox executor ------------------ #
class PythonExecutor:
    """Run user-generated code in a trimmed global scope; return structured result."""
    def __init__(self, workdir="tmp_exec", data_root="."):
        self.workdir = Path(workdir); self.workdir.mkdir(exist_ok=True)
        self.da = DataHub(root=data_root)  # shared across tool calls

    def tool_spec(self) -> str:
        return (
            "You can use the following Python tools available in the sandbox as `da`:\n"
            "- da.load(path[, sheet]) -> {df_id, n_rows, n_cols, columns, dtypes}\n"
            "- da.head(df_id, n=5) -> DataFrame\n"
            "- da.describe(df_id) -> {shape, na_per_col, sample_rows}\n"
            "- da.columns(df_id) -> list[str]\n"
            "- da.mean(df_id, col) -> float\n"
            "- da.groupby_nan_count(df_id, group_col) -> DataFrame[group, num_missing]\n"
            "- da.argmax_missing(df_id, group_col) -> {group, num_missing}\n"
            "Supported formats: .csv, .xlsx/.xls, .json\n"
            "Notes: CSV auto-encoding; JSON accepts list[dict] or dict with 'data' key.\n"
        )

    def run(self, code: str):
        """
        Execute user code in a trimmed global scope.

        Returns:
            dict{
              ok: bool,              # True if no exception
              stdout: str,           # captured prints (truncated)
              stderr: str,           # traceback or warnings (truncated)
            }
        """
        out_buf, err_buf = io.StringIO(), io.StringIO()
        g = {
            "pd": pd,
            "plt": plt,
            "da": self.da,
            "__name__": "__main__",
            "__file__": None
        }
        ok = True
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                exec(code, g)
            except Exception:
                ok = False
                # 将完整 traceback 写入 stderr
                traceback.print_exc()

        # 截断，避免超长消息污染对话
        stdout = textwrap.shorten(out_buf.getvalue(), 1600)
        stderr = textwrap.shorten(err_buf.getvalue(), 1600)

        # 兼容：如果你旧逻辑期望字符串，可用 isinstance(obs, dict) 分支判断
        return {"ok": ok and (not re.search(r"Traceback \(most recent call last\):", stderr or "")),
                "stdout": stdout,
                "stderr": stderr}


# ------------------ core InsightAgent ------------------ #
class InsightAgent:
    def __init__(self,
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.0,
                 max_tool_calls: int = 3,
                 data_root: str = "."):
        load_dotenv()
        self.exec = PythonExecutor(data_root=data_root)
        self.llm = OpenAIClient(model=model, temperature=temperature)
        self.temperature = temperature
        self.max_calls = max_tool_calls

        # 在 system prompt 里拼上工具说明，帮助 LLM 正确用法
        tool_spec = self.exec.tool_spec()
        self.system_prompt = f"{SYSTEM_PROMPT}\n\n# Tools\n{tool_spec}"

        # few-shots → 对话片段
        self.few_shots = []
        few_shot_tem = FEW_SHOT_SAMPLE
        for fs in few_shot_tem:
            self.few_shots.append(
                {"role": "user", "content": json.dumps(fs["input"], ensure_ascii=False)}
            )
            # 把 thought/code/obs 线性化
            shot_text = (
                f"Thought: {fs['assistant']['Thought']}\n"
                f"```python\n{fs['assistant']['Code']}\n```\n"
                f"Observation: {fs['assistant']['Observation']}\n"
                f"Final Answer: {json.dumps(fs['assistant']['Final'], ensure_ascii=False)}"
            )
            self.few_shots.append({"role": "assistant", "content": shot_text})

    # ---- OpenAI wrapper
    def _chat(self, messages):
        return self.llm.chat(messages)

    # ---- JSON extractor ----
    def extract_final_json(self, text: str):
        """
        Robustly extract the first JSON object in `text`.

        Priority:
        1) ```json ... ``` fenced block
        2) First balanced {...} scanning backwards
        """
        # ① fenced block
        json_block = re.search(r"```json\s*({[\s\S]*?})\s*```", text, re.I)
        if json_block:
            return json.loads(json_block.group(1))

        # ② backward scan for balanced braces
        stack, start, end = 0, None, None
        for i in range(len(text) - 1, -1, -1):
            ch = text[i]
            if ch == "}":
                if stack == 0:
                    end = i + 1
                stack += 1
            elif ch == "{":
                stack -= 1
                if stack == 0 and end is not None:
                    start = i
                    candidate = text[start:end]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        pass
        raise ValueError("No valid JSON object found in assistant output.")

        # ---- 主入口：跑单一样本
    def run_sample(self, sample: dict):
        sys_msg = {"role": "system", "content": self.system_prompt}
        user_msg = {"role": "user", "content": json.dumps({
            "question": sample["question"],
            "data_path": sample.get("data_file"),
            "analysis_type": sample.get("analysis_type"),
            "additional_information": sample.get("additional_information"),
        }, ensure_ascii=False)}
        conversation = [sys_msg] + self.few_shots + [user_msg]

        tool_calls = 0
        last_error_sig = None  # 用于检测重复错误，避免死循环
        last_code = None

        while True:
            assistant_out = self._chat(conversation)
            conversation.append({"role": "assistant", "content": assistant_out})
            print(f"Assistant: {assistant_out}")

            # ---- 抓 python 代码块
            match = re.search(r"```python\s*(.*?)```", assistant_out, re.S | re.I)
            if match and tool_calls < self.max_calls:
                code = match.group(1).strip()
                last_code = code
                obs  = self.exec.run(code)                     # 兼容你现有的 executor：返回纯文本
                tool_calls += 1

                # --- 识别是否报错（两种方式都支持）
                # 方式A：如果你把 executor 改造成返回 dict: {"ok":bool,"stdout":..., "stderr":...}
                if isinstance(obs, dict) and "ok" in obs:
                    ok = bool(obs.get("ok", False))
                    stdout = str(obs.get("stdout", "")).strip()
                    stderr = str(obs.get("stderr", "")).strip()
                    if ok:
                        conversation.append({"role": "user", "content": f"Observation:\n{stdout}"})
                        continue
                    else:
                        # 记录错误签名，避免死循环
                        err_sig = (stderr[:280] or "ERR")
                        # 若连续同样错误，直接退出循环，返回调试信息
                        if err_sig == last_error_sig:
                            conversation.append({"role": "user", "content": f"Observation:\n[[ERROR PERSISTED]]\n{stderr}\n"} )
                            break
                        last_error_sig = err_sig
                        # 要求模型基于错误修复代码，只返回代码块
                        repair_prompt = (
                            "Observation:\n[[ERROR]]\n"
                            + (stderr if stderr else stdout)
                            + "\n\nPlease fix the code based on the error above. "
                              "Return ONLY a corrected Python code block between ```python ... ```.\n"
                              "Constraints:\n"
                              "- Use the provided tools (da.load/da.columns/da.mean etc.).\n"
                              "- Do not access the internet or filesystem beyond data_path.\n"
                              "- Keep printing ONLY the final textual answer.\n\n"
                              "Here is the previous code for reference:\n"
                              f"```python\n{code}\n```"
                        )
                        conversation.append({"role": "user", "content": repair_prompt})
                        continue

                # 方式B：保持你原 executor 不变，抓取 stdout 里的 Traceback
                obs_text = str(obs)
                has_error = bool(re.search(r"Traceback \(most recent call last\):", obs_text))
                if not has_error:
                    conversation.append({"role": "user", "content": f"Observation:\n{obs_text}"})
                    continue
                else:
                    err_sig = obs_text.strip()[:280]
                    if err_sig == last_error_sig:
                        conversation.append({"role": "user", "content": f"Observation:\n[[ERROR PERSISTED]]\n{obs_text}\n"} )
                        break
                    last_error_sig = err_sig
                    repair_prompt = (
                        "Observation:\n[[ERROR]]\n" + obs_text +
                        "\n\nPlease fix the code based on the error above. "
                        "Return ONLY a corrected Python code block between ```python ... ```.\n"
                        "Constraints:\n"
                        "- Use the provided tools (da.load/da.columns/da.mean etc.).\n"
                        "- Do not access the internet or filesystem beyond data_path.\n"
                        "- Keep printing ONLY the final textual answer.\n\n"
                        "Here is the previous code for reference:\n"
                        f"```python\n{code}\n```"
                    )
                    conversation.append({"role": "user", "content": repair_prompt})
                    continue

            # ---- 抓 Final Answer JSON（如果你还在用旧格式）
            if "Final Answer" in assistant_out:
                try:
                    final_obj = self.extract_final_json(assistant_out)
                    return conversation, final_obj
                except Exception:
                    return conversation, {"raw_output": assistant_out}

            # ---- 新版只返回文本：直接把最后一条文本当答案
            # （避免使用 eval，防止安全风险）
            return conversation, {"answer": assistant_out.strip()}

if __name__ == "__main__":
    # 简单测试 InsightAgent
    import json
    from pathlib import Path

    # 构造一个测试样本（你可以替换成自己的 mini 数据文件）
    sample = {
    "id":"BLAD_0",
    "question":"<Instruction>\nGiven the research question and dataset, we want to perform an analysis to answer the question. \nSpecifically we want to operationalize the conceptual variable *gender of the loan applicant* which we will use for statistical modeling. \nOf the choices given, select transformation code that is LEAST justifiable to operationalize *gender of the loan applicant*.\"\n\nIn addition to the answer please also include a rationale.\nReturn your answer in the format specified below:\nThe output should be formatted as a JSON instance that conforms to the JSON schema below.\n\nAs an example, for the schema {\"properties\": {\"foo\": {\"title\": \"Foo\", \"description\": \"a list of strings\", \"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": [\"foo\"]}\nthe object {\"foo\": [\"bar\", \"baz\"]} is a well-formatted instance of the schema. The object {\"properties\": {\"foo\": [\"bar\", \"baz\"]}} is not well-formatted.\n\nHere is the output schema:\n```\n{\"properties\": {\"answer\": {\"enum\": [\"A\", \"B\", \"C\", \"D\"], \"title\": \"The answer to the multiple choice question\", \"type\": \"string\"}, \"rationale\": {\"title\": \"The rationale for the answer\", \"type\": \"string\"}}, \"required\": [\"answer\", \"rationale\"]}\n```\n</Instruction> \n\nResearch Question: How does gender affect whether banks approve an individual\u2019s mortgage application?\nDataset: {\n  \"dataset_description\": \"This dataset comes from an influential study of discrimination in mortgage lending conducted by the Federal Reserve Bank of Boston [(Munnell et al. 1996)](https://drive.google.com/drive/u/0/folders/1NExj9btC_jGo42u-DYP_Zd2LF40uuMGD).\\n\\nThe context is that previous Home Mortgage Disclosure Act (HMDA) data showed much higher loan denial rates for minorities compared to whites. However, the HMDA data lacked important variables related to creditworthiness, so it was unclear if the racial disparity was due to differences in applicant qualifications or discrimination.\\n\\nTo address this, researchers at the Federal Reserve Bank of Boston collected additional data from lenders in 1990 on financial, employment, and property characteristics of applicants. This included variables like credit history, debt ratios, loan-to-value ratios, and more that lenders use to evaluate loan applications. The data covered both accepted and denied mortgage applications.\",\n  \"fields\": [\n    {\n      \"column\": \"Unnamed: 0\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 687.1911427446273,\n        \"min\": 0,\n        \"max\": 2379,\n        \"samples\": [\n          1413,\n          2168,\n          2002\n        ],\n        \"num_unique_values\": 2380,\n        \"semantic_type\": \"\",\n        \"description\": \"\"\n      }\n    },\n    {\n      \"column\": \"female\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.4070866105412032,\n        \"min\": 0.0,\n        \"max\": 1.0,\n        \"samples\": [\n          0.0,\n          1.0\n        ],\n        \"num_unique_values\": 2,\n        \"semantic_type\": \"\",\n        \"description\": \"1 if applicant is female, 0 if male\"\n      }\n    },\n    {\n      \"column\": \"black\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.34957120526725943,\n        \"min\": 0,\n        \"max\": 1,\n        \"samples\": [\n          1,\n          0\n        ],\n        \"num_unique_values\": 2,\n        \"semantic_type\": \"\",\n        \"description\": \"1 if applicant is Black, 0 otherwise\"\n      }\n    },\n    {\n      \"column\": \"housing_expense_ratio\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.09665561118274041,\n        \"min\": 0.0,\n        \"max\": 3.0,\n        \"samples\": [\n          0.2883,\n          0.239,\n          0.2754\n        ],\n        \"num_unique_values\": 500,\n        \"semantic_type\": \"\",\n        \"description\": \"Housing expense as a ratio of total income\"\n      }\n    },\n    {\n      \"column\": \"self_employed\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.3207552853451009,\n        \"min\": 0,\n        \"max\": 1,\n        \"samples\": [\n          1,\n          0\n        ],\n        \"num_unique_values\": 2,\n        \"semantic_type\": \"\",\n        \"description\": \"1 if applicant is self-employed, 0 otherwise\"\n      }\n    },\n    {\n      \"column\": \"married\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.48846845077475415,\n        \"min\": 0.0,\n        \"max\": 1.0,\n        \"samples\": [\n          0.0,\n          1.0\n        ],\n        \"num_unique_values\": 2,\n        \"semantic_type\": \"\",\n        \"description\": \"1 if applicant is married, 0 otherwise\"\n      }\n    },\n    {\n      \"column\": \"mortgage_credit\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.5372816153447328,\n        \"min\": 1,\n        \"max\": 4,\n        \"samples\": [\n          1,\n          3,\n          2\n        ],\n        \"num_unique_values\": 4,\n        \"semantic_type\": \"\",\n        \"description\": \"Applicant's mortgage credit score\"\n      }\n    },\n    {\n      \"column\": \"consumer_credit\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 1.666720586480013,\n        \"min\": 1,\n        \"max\": 6,\n        \"samples\": [\n          5,\n          2,\n          4\n        ],\n        \"num_unique_values\": 6,\n        \"semantic_type\": \"\",\n        \"description\": \"Applicant's consumer credit score\"\n      }\n    },\n    {\n      \"column\": \"bad_history\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.26105836980012176,\n        \"min\": 0,\n        \"max\": 1,\n        \"samples\": [\n          1,\n          0\n        ],\n        \"num_unique_values\": 2,\n        \"semantic_type\": \"\",\n        \"description\": \"1 if applicant has history of bad credit, 0 otherwise\"\n      }\n    },\n    {\n      \"column\": \"PI_ratio\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.0827703577027466,\n        \"min\": 0.0,\n        \"max\": 0.95,\n        \"samples\": [\n          0.42200002,\n          0.2967,\n          0.39380002\n        ],\n        \"num_unique_values\": 515,\n        \"semantic_type\": \"\",\n        \"description\": \"Total debt payments to income ratio\"\n      }\n    },\n    {\n      \"column\": \"deny\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.32473473427038013,\n        \"min\": 0,\n        \"max\": 1,\n        \"samples\": [\n          1,\n          0\n        ],\n        \"num_unique_values\": 2,\n        \"semantic_type\": \"\",\n        \"description\": \"1 if mortgage application was denied, 0 if accepted\"\n      }\n    },\n    {\n      \"column\": \"loan_to_value\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.17875097714406177,\n        \"min\": 0.02,\n        \"max\": 1.95,\n        \"samples\": [\n          0.79113925,\n          0.88235295,\n          0.5503876\n        ],\n        \"num_unique_values\": 1537,\n        \"semantic_type\": \"\",\n        \"description\": \"Ratio of loan amount to appraised value of property\"\n      }\n    },\n    {\n      \"column\": \"denied_PMI\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.1406044908793718,\n        \"min\": 0,\n        \"max\": 1,\n        \"samples\": [\n          1,\n          0\n        ],\n        \"num_unique_values\": 2,\n        \"semantic_type\": \"\",\n        \"description\": \"1 if application was denied private mortgage insurance, 0 otherwise\"\n      }\n    },\n    {\n      \"column\": \"accept\",\n      \"properties\": {\n        \"dtype\": \"number\",\n        \"std\": 0.32473473427038013,\n        \"min\": 0,\n        \"max\": 1,\n        \"samples\": [\n          0,\n          1\n        ],\n        \"num_unique_values\": 2,\n        \"semantic_type\": \"\",\n        \"description\": \"1 if mortgage application was accepted, 0 if denied\"\n      }\n    }\n  ],\n  \"num_rows\": 2380,\n  \"field_names\": [\n    \"Unnamed: 0\",\n    \"female\",\n    \"black\",\n    \"housing_expense_ratio\",\n    \"self_employed\",\n    \"married\",\n    \"mortgage_credit\",\n    \"consumer_credit\",\n    \"bad_history\",\n    \"PI_ratio\",\n    \"deny\",\n    \"loan_to_value\",\n    \"denied_PMI\",\n    \"accept\"\n  ]\n}\n\nA.\n```python\ndf['married_male'] = df.apply(lambda row: 1 if row['female'] == 0 and row[\n    'married'] == 1 else 0, axis=1)\n\n```\nB.\n```python\nfrom sklearn.utils import resample\nmajority_class = df[df['accept'] == 1]\nminority_class = df[df['accept'] == 0]\nundersampled_majority = resample(majority_class, replace=False, n_samples=len(minority_class), random_state=0)\ndf = pd.concat([undersampled_majority, minority_class])\ndf = df[~df['female'].isna()]\ndf['impute_PI_ratio'] = df['PI_ratio'].fillna(df['PI_ratio'].median())\n```\nC.\n```python\ndf['male'] = df['female'].apply(lambda x: 0 if x == 1 else 1)\ndf['bad_credit_male'] = df.apply(lambda row: 1 if row['male'] == 1 and row[\n    'bad_history'] == 1 else 0, axis=1)\n\n```\nD.\n```python\ndf['self_employed_female'] = df.apply(lambda row: 1 if row['female'] == 1 and\n    row['self_employed'] == 1 else 0, axis=1)\n\n```\n\nThe valid values are: A, B, C, D\nAnswer: ",
    "data_file":"./overall_data/blad_data/mortgage/info.json",
    "doc_file":"None",
    "answer":"B",
    "data_domain":"Finance",
    "analysis_type":"Structure problems",
    "origin_from":[
      "DSBench",
      "mortgage"
    ],
    "additional_information":""
  }

    # 初始化 Agent
    agent = InsightAgent(
        model="gpt-4o-mini",    # 测试用小模型
        temperature=0.0,
        max_tool_calls=3,
        data_root=sample['data_file']          # 数据文件所在的根目录
    )

    # 执行
    print("[*] Running test sample...")
    conv, result = agent.run_sample(sample)

    # 打印结果
    print("\n=== Final Answer ===")
    print(result)
    print(result['raw_output']['answer'])