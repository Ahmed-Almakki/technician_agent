# Your Tech Guy

An AI-powered technical-support assistant that finds repair information from the [iFixit API](https://www.ifixit.com/), presents it in a Streamlit chat interface, and records agent activity with MLflow, PostgreSQL/pgvector, and OpenTelemetry tracing.

The agent is designed to give repair guidance only when it can retrieve relevant iFixit data. It can search for devices, find matching repair guides, retrieve guide steps and images, and reuse matching guide IDs stored in a vector database.

## Features

- Streamlit chat UI for asking device-repair questions.
- LangChain/LangGraph agent backed by Groq (`openai/gpt-oss-120b` by default).
- iFixit tools for device search, guide-category lookup, and detailed repair steps.
- HTML repair-guide responses with step text and iFixit images.
- Semantic lookup and persistence of guide IDs using PostgreSQL with pgvector.
- Lazy, cached Hugging Face embedding-model loading to avoid delaying initial UI startup.
- MLflow LangChain autologging and Tempo/Grafana observability services.

## Architecture

```text
Browser
   |
   v
Streamlit app (:8501)
   |
   v
LangChain agent ──────────────> Groq LLM
   |  |  |
   |  |  +--------------------> iFixit API
   |  +-----------------------> PostgreSQL + pgvector
   +--------------------------> MLflow (:5000) ──> PostgreSQL
                                  |
                                  +--------------> Tempo (:4317) ──> Grafana (:3000)
```

## Project layout

```text
app/tech_agent.py       Streamlit chat application
src/agent/config.py     LLM configuration and agent system prompt
src/agent/main.py       Agent construction, execution, and MLflow setup
src/tools/tools.py      iFixit, pgvector, and embedding-model tools
db/init.sql             pgvector extension, databases, and agent_history table
monitoring/tempo/       Tempo configuration
docker-compose.yaml     Local multi-service environment
Dockerfile              Python/uv runtime image
Dockerfile.db           PostgreSQL image with pgvector installed
```

## Prerequisites

- Python 3.13+ and [uv](https://docs.astral.sh/uv/) for local development.
- Docker Engine with Docker Compose for the full stack.
- A Groq API key.
- An embedding model for semantic guide lookup. To use a local model, mount it in Docker and set `EMBEDDING_MODEL_PATH` in `docker-compose.yaml` to its container path. Otherwise, configure `EMBEDDING_MODEL_PATH` with a Hugging Face model ID so it can be downloaded automatically the first time it is used.



## Run locally

First install the locked dependencies:

```bash
uv sync --frozen
```

Start PostgreSQL and MLflow before launching the UI. With the Compose services available, run:

```bash
uv run streamlit run app/tech_agent.py
```

After the environment has been synced, this avoids a dependency sync check on subsequent starts:

```bash
uv run --no-sync streamlit run app/tech_agent.py
```

Open <http://localhost:8501>.

The Makefile also provides:

```bash
make app          # Start the Streamlit app
make agent        # Run the agent module
make eval_agent   # Run MLflow evaluation code
make run          # Start Compose services in the background
```

## Run the full stack with Docker Compose

Build the images if they are not already available, then start the services:

```bash
docker compose up --build -d
docker compose ps
```

Service endpoints:

| Service | URL / port |
|---|---|
| Streamlit | <http://localhost:8501> |
| MLflow | <http://localhost:5000> |
| Grafana | <http://localhost:3000> |
| Adminer | <http://localhost:8081> |
| PostgreSQL | `localhost:5433` |
| Tempo | `localhost:3200` and OTLP gRPC `localhost:4317` |

Useful commands:

```bash
docker compose logs -f app
docker compose logs -f mlflow
docker compose down
```

Verify MLflow before opening the UI:

```bash
curl http://localhost:5000/health
```

## How a request is handled

1. Streamlit stores the user message and a per-browser-session UUID.
2. `run_agent()` creates a LangChain agent with the iFixit and database tools.
3. The LLM determines whether the request is valid and may use up to three iFixit searches.
4. For a matching repair guide, the agent retrieves official iFixit steps and image URLs.
5. The response is returned as HTML and rendered in an isolated Streamlit component.
6. The agent can embed a device/problem query, look up a previously stored guide ID in pgvector, and save new guide associations.
7. MLflow records LangChain traces; the Compose stack can export telemetry to Tempo for visualization in Grafana.

For best results, ask a clear question containing a device and problem, for example:

```text
My Nintendo Switch left Joy-Con joystick is drifting. Find the repair guide.
```

## Data model

`db/init.sql` creates the `agent_history` table:

| Column | Purpose |
|---|---|
| `query` | 768-dimensional embedding of the device/problem query |
| `guide_id` | iFixit guide identifier |
| `session_id` | Streamlit chat-session identifier |
| `created`, `updated` | Record timestamps |

It also enables the `vector` PostgreSQL extension and creates the MLflow database.

## Evaluation

The project includes an MLflow GenAI regression suite in `eval/eval_dataset.py` and `eval/run_eval.py`. The dataset covers successful guide retrieval, typos and misspellings, vague requests that require clarification, and edge cases such as out-of-scope requests and prompt-injection attempts.

The evaluation runs the agent against a small development subset and uses these MLflow scorers:

- `Correctness`
- `RetrievalRelevance`
- `RetrievalGroundedness`
- `ToolCallCorrectness`

Start MLflow, ensure your environment variables are configured, then run:

```bash
make eval_agent
```

Results are printed in the terminal and recorded in the configured MLflow experiment. The evaluation worker counts are intentionally set to `1` in `eval/run_eval.py`, so test cases and scorers run sequentially.

## License

No license is currently specified for this repository. Add a license file before distributing the project.
