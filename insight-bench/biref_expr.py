import os
from insightbench import benchmarks, agents

# Set OpenAI API Key
## Note I use the API from https://https://api.v3.cm, which you also can use it for using GPT, Claude, DeepSeek and any ohter LLM.
## Using API is GPU-free solution for IS researchers to conduct experiment.
os.environ["OPENAI_API_KEY"] = 'sk-xxx'


# Get Dataset
dataset_dict = benchmarks.load_dataset_dict("data/notebooks/flag-1.json")

# Run an Agent
agent = agents.Agent(
    model_name="gpt-4o-mini",
    max_questions=2,
    branch_depth=1,
    n_retries=2,
    savedir="results/sample",
)
pred_insights, pred_summary = agent.get_insights(
    dataset_csv_path=dataset_dict["dataset_csv_path"], return_summary=True
)


# Evaluate
score_insights = benchmarks.evaluate_insights(
    pred_insights=pred_insights,
    gt_insights=dataset_dict["insights"],
    score_name="rouge1",
)
score_summary = benchmarks.evaluate_summary(
    pred=pred_summary, gt=dataset_dict["summary"], score_name="rouge1"
)

# Print Score
print("score_insights: ", score_insights)
print("score_summary: ", score_summary)