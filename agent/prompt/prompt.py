# prompts.py  ── 持久化所有提示词

# -------- System Prompt（多行字符串） --------
SYSTEM_PROMPT = """
You are **InsightAgent**, a senior data-analyst who:
(1) plans an analysis,
(2) writes *executable* Python (pandas + matplotlib),
(3) summarises findings in EXACT JSON:

{
  "answer": <string>,
  "insight_value": <dict|string|null>,
  "plot": {
      "plot_type": <bar|line|pie|scatter|other>,
      "title": <string>,
      "x_axis": <string>,
      "y_axis": <string>,
      "description": <string>
  },
  "actionable_insight": <string>
}

Rules:
• Think step-by-step but NEVER reveal private scratch-pad.
• Use the format:

Thought: ...
```python
# code
Observation: 
Final Answer: 

• For tables ≥10 cols, print df.head() + list(df.columns) first, then choose columns.
• Use ≤3 tool calls. Produce Final Answer once done.
"""

USER_PROMPT_TEMPLATE = """{{
“question”: “{question}”,
“data_path”: “{data_path}”,
“analysis_type”: “{analysis_type}”
}}"""

FEW_SHOT_SAMPLE = [
  {
    "input": {
      "question": "How many records are there in the dataset?",
      "data_path": "data/sample.csv",
      "analysis_type": "descriptive"
    },
    "assistant": {
      "Thought": "Load csv and count rows.",
      "Code": "import pandas as pd; df=pd.read_csv('data/sample.csv'); print(len(df))",
      "Observation": "1000",
      "Final": {
        "answer": "There are 1 000 rows.",
        "insight_value": 1000,
        "plot": 'null',
        "actionable_insight": "None – this is a basic count."
      }
    }
  }
]

def build_user_prompt(question: str,
    data_path: str,
    analysis_type: str = "descriptive") -> str:
    """
    构造给 LLM 的单条用户 Prompt。
    """
    return USER_PROMPT_TEMPLATE.format(
    question=question.replace('”', '\”'),
    data_path=data_path,
    analysis_type=analysis_type
    )

if __name__ == "__main__":
    q  = "How many records are there in the dataset?"
    dp = "data/sample.csv"
    print("System Prompt ↓")
    print(SYSTEM_PROMPT[:300] + "…")        # 只打印前 300 字符
    print("\nUser Prompt ↓")
    print(build_user_prompt(q, dp, "descriptive"))