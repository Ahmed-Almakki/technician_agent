from dotenv import load_dotenv, find_dotenv
import mlflow
from mlflow.genai.scorers import Correctness, ToolCallCorrectness, RetrievalRelevance, RetrievalGroundedness
import os
import uuid

from src.agent.main import run_agent
from src.agent.config import llm
from .eval_dataset import df

load_dotenv(find_dotenv())

print("DEBUG GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))
model="groq:/llama-3.3-70b-versatile"

mlflow.set_experiment(os.getenv("EXPERIMENT_NAME"))


def evaluate_guide_selection(eval_df):
    """
    Checks if the agent selected the exact expected guide_id.
    """
    scores = []
    for expected_id, trace in zip(eval_df["expected_guide_id"], eval_df["trace"]):
        if expected_id is None:
            scores.append(1 if "fetch_ifixit_steps" not in trace.tool_names else 0)
            continue
            
        called_id = trace.get_tool_inputs("fetch_ifixit_steps").get("guide_id")
        scores.append(1 if str(called_id) == str(expected_id) else 0)
        
    return scores


def agent(query):
    session_id = str(uuid.uuid4())
    
    anwer = run_agent(query, llm, session_id)

    return anwer


# For Development phase
# Limit concurrent data items being evaluated (default is 10)
os.environ["MLFLOW_GENAI_EVAL_MAX_WORKERS"] = "1"

# Limit concurrent scorer execution (default is 10) - run scorers sequentially
os.environ["MLFLOW_GENAI_EVAL_MAX_SCORER_WORKERS"] = "1"

if __name__ == "__main__":
    # Use the MLflow 3.0+ GenAI evaluate function
    results = mlflow.genai.evaluate(
        predict_fn=agent,               
        data=df.head(5),
        scorers=[
            Correctness(model=model), 
            RetrievalRelevance(model=model),
            RetrievalGroundedness(model=model), 
            ToolCallCorrectness(model=model),
        ],
    )

    # View results
    print(f"Safety pass rate: {results.metrics.get('safety/pass_rate', 'N/A')}")
    print(f"Correctness pass rate: {results.metrics.get('correctness/pass_rate', 'N/A')}")