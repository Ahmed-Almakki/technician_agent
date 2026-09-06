from dotenv import load_dotenv, find_dotenv
from typing import Literal
import mlflow
from mlflow.genai.judges import make_judge
from mlflow.genai.scorers import Safety, Correctness, RelevanceToQuery, Guidelines, ToolCallCorrectness, ToolCallEfficiency, RetrievalRelevance, RetrievalGroundedness
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


clarification_metric = make_judge(
    name="asks_for_clarification",
    instructions=(
        "Evaluate whether the agent properly asks the user for the specific device model when the initial query is too vague.\n"
        "Score 1 if the agent asked for clarification for a vague query. "
        "Score 0 if the agent proceeded blindly or if it asked for clarification when the query was already clear.\n\n"
        "User Query: {{ inputs }}\n"
        "Agent Response: {{ outputs }}"
    ),
    feedback_value_type=Literal[0, 1],
    model=model
)


def agent(query):
    session_id = str(uuid.uuid4())
    
    anwer = run_agent(query, llm, session_id)

    return anwer

if __name__ == "__main__":
    # Use the MLflow 3.0+ GenAI evaluate function
    results = mlflow.genai.evaluate(
        predict_fn=agent,               
        data=df,
        scorers=[
            Safety(model=model),
            Correctness(model=model), 
            Guidelines(name="is_english", guidelines="The answer must be in HTML format", model=model),
            RelevanceToQuery(model=model),
            RetrievalRelevance(model=model),
            RetrievalGroundedness(model=model), 
            ToolCallCorrectness(model=model),
            ToolCallEfficiency(model=model),
            clarification_metric
        ],
    )

    # View results
    print(f"Safety pass rate: {results.metrics.get('safety/pass_rate', 'N/A')}")
    print(f"Correctness pass rate: {results.metrics.get('correctness/pass_rate', 'N/A')}")