import argparse, json, random, pprint, time, datetime, sys
from pathlib import Path
from tqdm import tqdm

from agent.base_agent_v2 import InsightAgent   # 根据实际包层级调整

# ------------------------------ helpers ------------------------------ #
def load_samples(path: str | Path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    if p.suffix.lower() == ".jsonl":
        samples = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        return samples
    # default .json
    text = p.read_text(encoding="utf-8")
    return json.loads(text)

def save_results(results, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] Saved ➜ {out_path}")

# --------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/BA_data_v5.json",
                        help="evaluation samples (.json or .jsonl)")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--temp", type=float, default=0.0, help="LLM temperature")
    parser.add_argument("--max-calls", type=int, default=3, help="max tool calls per sample")
    parser.add_argument("--n", type=int, default=50,
                        help="number of samples (<=0 → all)")
    parser.add_argument("--out", type=str, default=None,
                        help="output json path (default results/<timestamp>.json)")
    parser.add_argument("--save-every", type=int, default=0,
                        help="checkpoint every K samples (0 disables)")
    parser.add_argument("--keep-conv", action="store_true",
                        help="store full conversation in results (large)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # 读取样本
    samples = load_samples(args.data)
    total = len(samples)
    random.seed(args.seed)
    if args.n > 0:
        # 随机抽样但保持可复现
        idxs = list(range(total))
        random.shuffle(idxs)
        samples = [samples[i] for i in idxs[:args.n]]

    # 运行 Agent
    agent = InsightAgent(
            model=args.model,
            temperature=args.temp,
            max_tool_calls=args.max_calls,
            data_root='.'
        )

    results, succeeded, failed = [], 0, 0
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    out_path = Path(args.out) if args.out else out_dir / f"results_{ts}.json"

    for k, samp in enumerate(tqdm(samples, desc="Running"), start=1):
        st = time.time()
        try:
            conv, res = agent.run_sample(samp)
            samp["elapsed_sec"] = round(time.time() - st, 2)
            samp["agent_out"] = res
            if args.keep_conv:
                samp["agent_conv"] = conv  # 体积较大，默认不保存
            else:
                samp["agent_conv"] = None
            results.append(samp)
            pprint.pp(res)
            succeeded += 1
        except Exception as e:
            # 单样本失败不终止整批运行
            err_msg = f"{type(e).__name__}: {e}"
            samp["elapsed_sec"] = round(time.time() - st, 2)
            samp["agent_out"] = {"error": err_msg}
            # samp["agent_out"] = res
            if args.keep_conv:
                samp["agent_conv"] = None
            results.append(samp)
            failed += 1
            print(f"[WARN] sample failed: {samp.get('id', k)} → {err_msg}", file=sys.stderr)

        # 周期性保存，防止长跑中断丢失
        if args.save_every and (k % args.save_every == 0):
            ckpt_path = out_dir / f"results_{ts}_k{k}.json"
            save_results(results, ckpt_path)

    # 最终保存
    save_results(results, out_path)
    print(f"[STATS] total={len(samples)} ok={succeeded} fail={failed}")

# --------------------------------------------------------------------- #
if __name__ == "__main__":
    main()