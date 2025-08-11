#!/bin/bash
set -e

# ---------- 参数设置 ----------
N=50                                           # 默认抽样数量（<=0 表示全部）
DATA_PATH="./BA_data_v6_mini.json" # 数据文件路径
DATA_ROOT="."                                   # 数据文件根目录
MODEL="gpt-4o"                                  # 模型名称
TEMP=0.0                                        # LLM temperature
MAX_CALLS=3                                     # 每个样本最大 tool 调用次数

# ---------- 输出路径 ----------
STAMP=$(date "+%Y%m%d_%H%M%S")
OUT_DIR="./results"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/results_v4.json"

# ---------- 运行 Agent ----------
echo "[*] Running InsightAgent ..."
python run.py \
  --data "$DATA_PATH" \
  --model "$MODEL" \
  --temp "$TEMP" \
  --max-calls "$MAX_CALLS" \
  --n "$N" \
  --out "$OUT_FILE" \
  --keep-conv

echo "[✓] Done. Results saved to $OUT_FILE"

# ---------- 评估结果 ---------- #
# ---------- 评估结果 ---------- #
EVAL_JSON="$OUT_DIR/eval_${STAMP}.json"
EVAL_CSV="$OUT_DIR/eval_${STAMP}.csv"

# LLM-as-Judge：通过环境变量开关（JUDGE=1 开启），可自定义评审模型
JUDGE="0"
JUDGE_MODEL="gpt-4o"

echo "[*] Evaluating results ..."
python eval_agent.py \
  --pred "$OUT_FILE" \
  --gold "$DATA_PATH" \
  --json "$EVAL_JSON" \
  --csv "$EVAL_CSV" \
  --judge "$JUDGE" \
  --judge-model "$JUDGE_MODEL"

echo "[✓] Eval saved:"
echo "    JSON: $EVAL_JSON"
echo "    CSV : $EVAL_CSV"


# echo "[*] Evaluating ..."
# python eval.py \
#        --pred $OUT_FILE \
#        --gold $DATA_PATH \
#        --model $MODEL \
#        --eval_path $EVAL_FILE \
#        --judge 
# echo "[✓] Done. Evaluation results saved to $EVAL_FILE"