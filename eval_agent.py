# eval_agent.py
# Evaluate InsightAgent outputs: Acc / EM / ROUGE / (optional) LLM-as-Judge.

import argparse, json, math, re, statistics, csv
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# -------------------------- Text normalization -------------------------- #
def normalize_text(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    # strip punctuation around tokens
    s = re.sub(r"[^\w\s\.\-\+\%/]", " ", s)  # keep numbers & common symbols
    s = re.sub(r"\s+", " ", s).strip()
    return s

def exact_match(pred: str, gold: str) -> int:
    return int(normalize_text(pred) == normalize_text(gold))

# -------------------------- ROUGE (1 & L) -------------------------- #
def _tokens(s: str) -> List[str]:
    return normalize_text(s).split()

def rouge1_f1(pred: str, gold: str) -> float:
    p = _tokens(pred); g = _tokens(gold)
    if not p or not g: return 0.0
    from collections import Counter
    pc, gc = Counter(p), Counter(g)
    overlap = sum((pc & gc).values())
    prec = overlap / len(p)
    rec  = overlap / len(g)
    if prec + rec == 0: return 0.0
    return 2 * prec * rec / (prec + rec)

def lcs(a: List[str], b: List[str]) -> int:
    # LCS length O(nm) DP, fine for short answers
    n, m = len(a), len(b)
    dp = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n):
        ai = a[i]
        for j in range(m):
            if ai == b[j]:
                dp[i+1][j+1] = dp[i][j] + 1
            else:
                dp[i+1][j+1] = max(dp[i][j+1], dp[i+1][j])
    return dp[n][m]

def rougeL_f1(pred: str, gold: str) -> float:
    p = _tokens(pred); g = _tokens(gold)
    if not p or not g: return 0.0
    l = lcs(p, g)
    prec = l / len(p)
    rec  = l / len(g)
    if prec + rec == 0: return 0.0
    return 2 * prec * rec / (prec + rec)

# -------------------------- Numeric helpers -------------------------- #
def to_float(x) -> Optional[float]:
    if x is None: return None
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip()
    # remove commas and currency
    s = re.sub(r"[,\$€¥]", "", s)
    try:
        return float(s)
    except:
        return None

def num_close(a, b, atol=1e-2, rtol=1e-2) -> bool:
    fa, fb = to_float(a), to_float(b)
    if fa is None or fb is None: return False
    return abs(fa - fb) <= max(atol, rtol * abs(fb))

# -------------------------- Type detection -------------------------- #
def detect_task_type(gold_answer) -> str:
    """
    Returns: 'mcq' | 'struct' | 'text'
    mcq: gold is a short string like 'A' / 'B'...
    struct: gold is list of [key, value] pairs
    text: otherwise
    """
    if isinstance(gold_answer, str) and re.fullmatch(r"[A-Za-z]", gold_answer.strip()):
        return "mcq"
    if isinstance(gold_answer, list) and all(isinstance(x, list) and len(x) == 2 for x in gold_answer):
        return "struct"
    return "text"
def requires_rationale(question_text: str) -> bool:
    if not isinstance(question_text, str): return False
    # 粗检：题干里出现 schema 且要求 ["answer","rationale"]
    q = question_text.lower()
    return ("output schema" in q or "here is the output schema" in q) and \
           ("\"required\": [\"answer\", \"rationale\"]" in q.replace(" ", "").lower())


# -------------------------- Prediction extraction -------------------------- #
def get_pred_text(record: Dict[str, Any]) -> str:
    """
    From a result record produced by main.py:
    - Prefer record["agent_out"] if string.
    - If dict, try common keys.
    - Else, fallback to str(record["agent_out"])
    """
    pred = record.get("agent_out", "")
    if isinstance(pred, str):
        return pred.strip()
    if isinstance(pred, dict):
        # try typical keys
        for k in ["answer", "final", "text", "prediction"]:
            if k in pred and isinstance(pred[k], str):
                return pred[k].strip()
        return json.dumps(pred, ensure_ascii=False)
    return str(pred).strip()

def extract_letter_and_rationale(pred_text: str) -> tuple[str, str]:
    """返回 (letter, rationale_text)"""
    text = pred_text.strip()
    # 抓首个 A-D 字母作为选项
    m = re.search(r"\b([A-Da-d])\b", text)
    letter = m.group(1).upper() if m else ""
    # 抓 rationale
    rat = ""
    # 1) 常见格式：Rationale: ...
    m2 = re.search(r"rationale\s*[:：]\s*(.+)", text, re.I | re.S)
    if m2:
        rat = m2.group(1).strip()
    else:
        # 2) 如果有 "Answer: X"，取其后文本
        m3 = re.search(r"answer\s*[:：]\s*[A-Da-d]\s*(.*)", text, re.I | re.S)
        if m3:
            rat = m3.group(1).strip()
        else:
            # 3) 退化：把去掉首个字母的剩余句子当 rationale
            if letter:
                idx = text.upper().find(letter)
                rat = text[idx+1:].strip() if idx >= 0 else ""
    return letter, rat

# For struct gold, try to parse values from pred text
def parse_struct_pred_text(pred_text: str, gold_pairs: List[List[Any]]) -> Dict[str, Any]:
    """
    Heuristic extraction: for each gold key, find trailing number in pred_text near the key.
    If not found, fallback to first number occurrence for that key.
    """
    res = {}
    lower = pred_text.lower()
    for k, _ in gold_pairs:
        k_str = str(k).strip()
        k_pat = re.escape(k_str.lower())
        # find a window around the key
        m = re.search(k_pat + r".{0,40}?", lower)
        if m:
            win = pred_text[m.start(): m.end()+40]
            num = re.search(r"[-+]?\d+(?:\.\d+)?", win)
            if num:
                res[k_str] = num.group(0)
                continue
        # fallback: any number in whole text
        num2 = re.search(r"[-+]?\d+(?:\.\d+)?", pred_text)
        if num2:
            res[k_str] = num2.group(0)
        else:
            res[k_str] = None
    return res

# -------------------------- LLM-as-Judge -------------------------- #
def llm_judge_score(client, model: str, question: str, gold, pred_text: str) -> float:
    """
    Returns 0-5 score. Implemented via your OpenAIClient-like wrapper.
    """
    gold_view = gold if isinstance(gold, str) else json.dumps(gold, ensure_ascii=False)
    prompt = (
        "You are a strict evaluator. Score how well the **Answer** satisfies the **Task** "
        "and aligns with the **Gold** reference.\n"
        "Return ONLY a number from 0 to 5 (integers allowed), no text.\n\n"
        f"Task: {question}\n"
        f"Gold: {gold_view}\n"
        f"Answer: {pred_text}\n"
    )
    msg = [{"role":"system","content":"You are a concise evaluator."},
           {"role":"user","content":prompt}]
    out = client.chat(msg).strip()
    m = re.search(r"\d+(?:\.\d+)?", out)
    if not m: return 0.0
    try:
        v = float(m.group(0))
        return max(0.0, min(5.0, v))
    except:
        return 0.0

# -------------------------- Evaluation per record -------------------------- #
def eval_record(rec: Dict[str, Any], llm_client=None, llm_model=None,
                atol=1e-2, rtol=1e-2) -> Dict[str, Any]:
    qtext = rec.get("question", "")
    need_rat = requires_rationale(qtext)
    gold = rec.get("answer")
    ttype = detect_task_type(gold)
    pred_text = get_pred_text(rec)

    out = {"id": rec.get("id"), "type": ttype, "pred": pred_text}

    if ttype == "mcq":
        gold_s = str(gold).strip().upper()
        pred_letter, pred_rat = extract_letter_and_rationale(pred_text)
        acc = int(pred_letter == gold_s)
        out.update(dict(
            gold=gold_s, acc=acc,
            em=exact_match(pred_text, gold_s),
            rouge1=rouge1_f1(pred_text, gold_s),
            rougeL=rougeL_f1(pred_text, gold_s),
        ))
        if need_rat:
            out["rationale_present"] = int(bool(pred_rat))
            if llm_client and llm_model and pred_rat:
                out["judge_rationale"] = llm_judge_score(
                    llm_client, llm_model,
                    f"Evaluate the quality of the rationale justifying why option {pred_letter} is chosen.",
                    f"Gold answer is {gold_s}. Rationale should justify least/most justifiable choice as asked.",
                    pred_rat
                )
            else:
                out["judge_rationale"] = None
        else:
            out["rationale_present"] = None
            out["judge_rationale"] = None
    elif ttype == "struct":
        # gold is list of [key, value]
        gold_map = {str(k): v for k, v in gold}
        pred_map = parse_struct_pred_text(pred_text, gold)
        keys_ok = all(k in pred_map for k in gold_map)
        vals_ok = keys_ok and all(num_close(pred_map[k], gold_map[k], atol, rtol) for k in gold_map)
        out.update(dict(gold=gold_map, parsed=pred_map, acc=int(vals_ok)))
        # 文本类指标也给一下参考
        out.update(dict(em=0, rouge1=0.0, rougeL=0.0))
    else:  # text
        gold_text = json.dumps(gold, ensure_ascii=False) if not isinstance(gold, str) else gold
        out.update(dict(
            gold=gold_text,
            acc=0,  # 无法定义准确率，用 EM/ROUGE/LLM 反映
            em=exact_match(pred_text, gold_text),
            rouge1=rouge1_f1(pred_text, gold_text),
            rougeL=rougeL_f1(pred_text, gold_text),
        ))

    if llm_client and llm_model:
        try:
            score = llm_judge_score(llm_client, llm_model, rec.get("question",""), gold, pred_text)
        except Exception:
            score = 0.0
        out["judge"] = score
    else:
        out["judge"] = None

    return out

# -------------------------- IO helpers -------------------------- #
def load_results(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    # data is list of sample dicts (as saved by main)
    return data

def align_with_gold(results: List[Dict[str, Any]], gold_path: Optional[str]) -> List[Dict[str, Any]]:
    if not gold_path:
        return results
    gold_list = json.loads(Path(gold_path).read_text(encoding="utf-8"))
    gmap = {g["id"]: g for g in gold_list}
    merged = []
    for r in results:
        rid = r.get("id")
        if rid in gmap:
            base = gmap[rid].copy()
            base.update(r)  # keep agent_out etc.
            merged.append(base)
        else:
            merged.append(r)
    return merged

def write_csv(details: List[Dict[str, Any]], csv_path: Path):
    keys = ["id","type","acc","em","rouge1","rougeL","judge","pred","gold"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for d in details:
            row = {k: d.get(k) for k in keys}
            # shorten long fields
            if isinstance(row.get("pred"), str) and len(row["pred"])>100:
                row["pred"] = row["pred"][:100]+"..."
            if isinstance(row.get("gold"), str) and len(row["gold"])>100:
                row["gold"] = row["gold"][:100]+"..."
            w.writerow(row)

# -------------------------- Aggregation -------------------------- #
def summarize(details: List[Dict[str, Any]]):
    by_type = {"mcq": [], "struct": [], "text": []}
    for d in details:
        by_type.setdefault(d["type"], []).append(d)

    def avg(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs)/len(xs) if xs else 0.0

    summary = {}
    for t, rows in by_type.items():
        if not rows: 
            summary[t] = {}
            continue
        acc = avg([r.get("acc",0) for r in rows])
        em  = avg([r.get("em",0) for r in rows])
        r1  = avg([r.get("rouge1",0.0) for r in rows])
        rL  = avg([r.get("rougeL",0.0) for r in rows])
        jd  = avg([r.get("judge") for r in rows if r.get("judge") is not None])
        summary[t] = {"size": len(rows), "acc": acc, "em": em, "rouge1": r1, "rougeL": rL, "judge": jd}

    # overall
    all_rows = details
    overall = {
        "size": len(all_rows),
        "acc": avg([r.get("acc",0) for r in all_rows]),
        "em":  avg([r.get("em",0) for r in all_rows]),
        "rouge1": avg([r.get("rouge1",0.0) for r in all_rows]),
        "rougeL": avg([r.get("rougeL",0.0) for r in all_rows]),
        "judge": avg([r.get("judge") for r in all_rows if r.get("judge") is not None]),
    }
    return {"overall": overall, "by_type": summary}

# -------------------------- Main -------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True, help="results_xxx.json (from main.py)")
    ap.add_argument("--gold", default=None, help="optional, BA_data_xxx.json for alignment")
    ap.add_argument("--csv",  default=None, help="optional, path to save per-sample CSV")
    ap.add_argument("--json", default=None, help="optional, path to save details+summary JSON")
    ap.add_argument("--atol", type=float, default=1e-2)
    ap.add_argument("--rtol", type=float, default=1e-2)
    ap.add_argument("--judge",  type=str, help="enable LLM-as-Judge for text tasks")
    ap.add_argument("--judge-model", default="gpt-4o-mini")
    args = ap.parse_args()

    results = load_results(args.pred)
    results = align_with_gold(results, args.gold)

    # lazy import user client if needed
    llm_client = None
    if args.judge == '1':
        try:
            from agent.model.openai_api import OpenAIClient
            llm_client = OpenAIClient(model=args.judge_model, temperature=0.0)
        except Exception as e:
            print(f"[WARN] LLM-as-Judge disabled: {e}")
            llm_client = None

    details = []
    for rec in results:
        d = eval_record(rec, llm_client if args.judge else None, args.judge_model if args.judge else None,
                        atol=args.atol, rtol=args.rtol)
        details.append(d)

    summary = summarize(details)

    # print summary
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # outputs
    if args.csv:
        write_csv(details, Path(args.csv))
        print(f"[INFO] wrote CSV → {args.csv}")
    if args.json:
        payload = {"summary": summary, "details": details}
        Path(args.json).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[INFO] wrote JSON → {args.json}")

if __name__ == "__main__":
    main()
