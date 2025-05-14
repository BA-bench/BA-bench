#!/usr/bin/env bash

# ---------- 解析参数 ---------- #
N=10                              # 默认抽样 10 条
DATA_PATH="./BA_data_v6(overall_datapath).json" # 默认基准文件
MODEL="gpt-4o"
# ---------------- 输出路径 ---------------- #
STAMP=$(date "+%Y%m%d_%H%M%S") 
OUT_DIR="./results"
OUT_FILE="$OUT_DIR/results_v2.json"
EVAL_FILE="$OUT_DIR/eval_v2.csv"
# ---------- 运行 Agent ---------- #
echo "[*] Running InsightAgent ..."
# python run.py \
#  --data $DATA_PATH \
#  --model $MODEL \
#  --n $N \
#  --out $OUT_FILE

echo "[✓] Done. Results saved to $OUT_FILE"

# ---------- 评估结果 ---------- #
echo "[*] Evaluating ..."
python eval.py \
       --pred $OUT_FILE \
       --gold $DATA_PATH \
       --model $MODEL \
       --eval_path $EVAL_FILE \
       --judge 
echo "[✓] Done. Evaluation results saved to $EVAL_FILE"