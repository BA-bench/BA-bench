"""
evaluate.py  (v2)
---------------
整体 + 按 analysis_type + 按 data_domain 评估结果，并导出明细 CSV
用法:
    python evaluate.py --pred results.json --gold data/BA_data_v5.json
"""

import argparse, json, math, re, statistics
from collections import defaultdict
from pathlib import Path

import openai
import pandas as pd
from agent.model.openai_api import OpenAIClient

# ---------------- GPT-Judge Prompt ---------------- #
JUDGE_PROMPT = """You are a meticulous evaluator.
Task: Give a score 0–5 (5 = perfect, 0 = totally wrong) judging
whether ASSISTANT_ANSWER answers USER_QUESTION with respect to GOLD_REFERENCE.
Return ONLY the number.
"""

def gpt_score(q, a, gold,llm):
    msgs = [
        {"role": "system", "content": JUDGE_PROMPT},
        {"role": "user",
         "content": f"USER_QUESTION:\n{q}\n\nGOLD_REFERENCE:\n{gold}\n\n"
                    f"ASSISTANT_ANSWER:\n{a}"}]
    resp = llm.chat(msgs)
    number = re.findall(r"[-+]?\d*\.\d+|\d+", resp)[0]
    return float(number)

def normalize(s): return re.sub(r"\s+", "", str(s).lower())
def em(pred, gold): return normalize(pred) == normalize(gold)
def num_close(pred, gold, tol=1e-3):
    try: return abs(float(pred) - float(gold)) <= tol
    except: return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--sample_key", default="question_id")
    ap.add_argument("--eval_path", default="question_id")
    ap.add_argument("--judge", action="store_true",
                    help="use GPT-Judge for open-ended tasks")
    ap.add_argument("--model", default="gpt-4o")
    args = ap.parse_args()

    preds = json.loads(Path(args.pred).read_text())
    golds = json.loads(Path(args.gold).read_text())
    llm = OpenAIClient(model= args.model,temperature= 0.0)

    # 若无 id 字段，用索引对齐
    if args.sample_key not in golds[0]:
        for i, g in enumerate(golds): g[args.sample_key] = i
        for i, p in enumerate(preds): p[args.sample_key] = i

    gold_map = {g[args.sample_key]: g for g in golds}

    # 统计器
    overall = {"total": 0, "correct": 0}
    by_type   = defaultdict(lambda: {"total": 0, "correct": 0})
    by_domain = defaultdict(lambda: {"total": 0, "correct": 0})

    detail_rows = []

    for p in preds:
        gid = p[args.sample_key]
        g   = gold_map.get(gid)
        if g is None: continue

        a_type = g["analysis_type"]
        domain = g.get("data_domain", "unknown")

        pred_ans, gold_ans = p.get("answer"), g["answer"]
        is_correct = False

        # ---------- 闭式任务：Exact / 数值 ---------- #
        # if isinstance(gold_ans, (int, float, str)):
        if len(gold_ans)<5:
            is_correct = num_close(pred_ans, gold_ans) or em(pred_ans, gold_ans)

        # ---------- 开式任务：用 GPT 判分 ---------- #
        else:
            if args.judge:
                score = gpt_score(g["question"], str(pred_ans), str(gold_ans),llm)
                print(score)
            else:
                score = 0             # 若关闭 judge，全部算错
            p["gpt_score"] = score
            is_correct = score >= 4

        # 更新统计
        for bucket in (overall, by_type[a_type], by_domain[domain]):
            bucket["total"]   += 1
            bucket["correct"] += int(is_correct)

        # 保存明细
        detail_rows.append({
            "id": gid,
            "analysis_type": a_type,
            "data_domain": domain,
            "gold_answer": gold_ans,
            "pred_answer": pred_ans,
            "correct": int(is_correct),
            "gpt_score": p.get("gpt_score", None)
        })

    # ---------- 打印结果 ---------- #
    def fmt(bkt): return bkt["correct"], bkt["total"], bkt["correct"]/bkt["total"]
    print("\n=== Overall ===")
    c, t, acc = fmt(overall); print(f"  {c}/{t}  (acc={acc:.1%})")

    print("\n=== By analysis_type ===")
    # print(by_type)
    for k, b in sorted(by_type.items()):
        c, t, a = fmt(b); print(f"  {k:<12}  {c}/{t}  {a:.1%}")

    print("\n=== By data_domain ===")
    print(by_domain)
    def sort_key(item):
        key, _ = item
        return (key is None, str(key)) 
    for k, b in sorted(by_domain.items(), key=sort_key):
        label = "none" if k is None else k
        c, t, a = fmt(b)
        print(f"{label:<12} {c}/{t} {a:.1%}")

    # ---------- 导出明细 CSV ---------- #
    df = pd.DataFrame(detail_rows)
    df.to_csv(args.eval_path, index=False)
    print(f"\nSaved 👉 {args.eval_path}  (per-sample results)")

if __name__ == "__main__":
    main()