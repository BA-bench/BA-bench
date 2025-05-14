import argparse, json, random, pprint, time, datetime
from pathlib import Path
from tqdm import tqdm

from agent.base_agent import InsightAgent   # 根据实际包层级调整

# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/BA_data_v5.json")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--n", type=int, default=5,
                        help="number of samples (<=0 → all)")
    parser.add_argument("--out", type=str, default=None,
                        help="output json path (default results/<timestamp>.json)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # 读取样本
    samples = json.loads(Path(args.data).read_text())
    random.seed(args.seed)
    if args.n > 0:
        samples = random.sample(samples, args.n)

    # 运行 Agent
    agent = InsightAgent(model= args.model,temperature= 0.0)
    results = []
    for samp in tqdm(samples, desc="Running"):
        st = time.time()
        conv,res = agent.run_sample(samp)
        # if 'error' in res.keys():
        #     res['error'] = str(res['error'])
        # res = {"error": str(e)}
        samp["elapsed_sec"] = round(time.time() - st, 2)
        samp['agent_out'] = res
        samp['agent_conv'] = conv
        results.append(samp)
        pprint.pp(res)

    # -------- 保存到 results/ 目录，文件名带时间戳 -------- #
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    if args.out:                      # 如果 run.sh 传了 --out 就用
        out_path = Path(args.out)
    else:                             # 否则自动时间戳
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"results_{ts}.json"

    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Saved ➜ {out_path}")

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()