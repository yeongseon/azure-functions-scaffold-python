# AI Agents Example

Two templates serve AI workloads: **ai** for direct Azure OpenAI integration
and **langgraph** for LangGraph agent deployment. This walkthrough covers both.

## What You Will Build

By the end, you will have:

- an Azure OpenAI chat endpoint that accepts prompts and returns completions
- or a LangGraph agent deployed as an Azure Functions app
- local run and test verification for either template

## 1) Generate an Azure OpenAI Project

```bash
afs advanced new --template ai --preset standard my-ai-api
```

Set up environment and dependencies:

```bash
cd my-ai-api
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Run quality checks:

```bash
make check-all
```

## 2) Understand the Chat Endpoint

The generated function exposes a `POST /api/chat` endpoint:

```python
@ai_blueprint.route(
    route="chat",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        prompt = body.get("prompt", "")
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON body."}),
            status_code=400,
            mimetype="application/json",
        )

    if not prompt:
        return func.HttpResponse(
            body=json.dumps({"error": "Missing 'prompt' field."}),
            status_code=400,
            mimetype="application/json",
        )

    result = await generate_completion(prompt)
    logging.info("Generated completion for prompt: %s", prompt[:50])
    return func.HttpResponse(
        body=json.dumps({"response": result}),
        status_code=200,
        mimetype="application/json",
    )
```

The service layer uses `AsyncAzureOpenAI` from the `openai` package:

```python
async def generate_completion(prompt: str) -> str:
    client = AsyncAzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version="2024-02-01",
    )
    response = await client.chat.completions.create(
        model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    return response.choices[0].message.content or ""
```

## 3) Configure Azure OpenAI Credentials

```bash
cp local.settings.json.example local.settings.json
```

Edit `local.settings.json` with your Azure OpenAI resource values:

| Setting | Description |
| :--- | :--- |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI resource endpoint URL. |
| `AZURE_OPENAI_API_KEY` | API key for authentication. |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name (defaults to `gpt-4o`). |

## 4) Run and Test the Chat Endpoint

```bash
func start
```

In a second terminal:

```bash
curl -X POST "http://localhost:7071/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is Azure Functions?"}'
```

Expected response shape:

```json
{"response": "Azure Functions is a serverless compute service..."}
```

## 5) AI Template Testing Strategy

The generated test validates input handling without calling Azure OpenAI:

```python
def test_chat_rejects_missing_prompt() -> None:
    request = func.HttpRequest(
        method="POST",
        url="http://localhost/api/chat",
        params={},
        body=json.dumps({"prompt": ""}).encode(),
        headers={"Content-Type": "application/json"},
    )

    import asyncio

    response = asyncio.run(chat(request))

    assert response.status_code == 400
```

Run tests:

```bash
pytest
```

!!! tip "Testing with mocks"
    For integration-level tests, mock `generate_completion` to avoid
    real API calls. Test service logic separately in `app/services/`.

## 6) Generate a LangGraph Agent Project

```bash
afs ai agent my-agent
```

Set up environment and dependencies:

```bash
cd my-agent
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Run quality checks:

```bash
make check-all
```

## 7) Understand the LangGraph Scaffold

The generated project has a different structure from other templates.

`app/graphs/echo_agent.py` defines a `StateGraph` with a single echo node:

```python
class AgentState(TypedDict):
    messages: list[dict[str, str]]


def chat(state: AgentState) -> dict:
    user_msg = state["messages"][-1]["content"]
    return {
        "messages": state["messages"]
        + [{"role": "assistant", "content": f"Echo: {user_msg}"}]
    }


builder = StateGraph(AgentState)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)
graph = builder.compile()
```

`function_app.py` uses `LangGraphApp` from `azure_functions_langgraph` to
expose the graph as Azure Functions endpoints:

```python
from azure_functions_langgraph import LangGraphApp
from app.graphs.echo_agent import graph

lg_app = LangGraphApp(auth_level=func.AuthLevel.ANONYMOUS)
lg_app.register(graph=graph, name="echo_agent")
func_app = lg_app.function_app
```

## 8) Run and Test the Agent

```bash
func start
```

Invoke the agent endpoint from a second terminal:

```bash
curl -X POST "http://localhost:7071/api/echo_agent" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"human","content":"Hello!"}]}'
```

The generated test invokes the graph directly without running the server:

```python
def test_echo_agent_invokes_successfully() -> None:
    result = graph.invoke(
        {"messages": [{"role": "human", "content": "Hello!"}]}
    )
    assert len(result["messages"]) == 2
    assert result["messages"][-1]["role"] == "assistant"
    assert "Echo: Hello!" in result["messages"][-1]["content"]
```

Run tests:

```bash
pytest
```

!!! note "LangGraph documentation"
    For deeper LangGraph configuration — tools, multi-step graphs, LLM
    integration — see the
    [azure-functions-langgraph](https://github.com/yeongseon/azure-functions-langgraph-python)
    documentation.

## 9) Customization Patterns

**AI template**:

- Swap the model deployment name via `AZURE_OPENAI_DEPLOYMENT`.
- Add a system prompt to the `messages` list in `generate_completion`.
- Integrate with other Azure AI services by adding service functions.

**LangGraph template**:

- Replace the echo node with a real LLM-backed node.
- Add tool nodes for retrieval, API calls, or database access.
- Build multi-step graphs by adding nodes and edges to the `StateGraph`.

!!! tip "Keep graphs in app/graphs/"
    Follow the generated pattern: define graphs in `app/graphs/`, register
    them in `function_app.py`, and test graph logic independently of the
    Azure Functions runtime.

## Troubleshooting Notes

!!! warning "401 Unauthorized from Azure OpenAI"
    Verify `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY` in
    `local.settings.json`. Confirm the API key is active and the endpoint
    URL is correct.

!!! warning "Module not found errors"
    Confirm all dependencies are installed. The AI template requires the
    `openai` package. The LangGraph template requires `langgraph` and
    `azure-functions-langgraph`.

!!! warning "Empty response from chat endpoint"
    Check that `AZURE_OPENAI_DEPLOYMENT` matches an existing deployment in
    your Azure OpenAI resource.

## Next Steps

- See [HTTP API](http_api.md) for REST API patterns with OpenAPI and validation.
- See [Full Stack](full_stack.md) for production baseline configuration.
- See [Templates](../guide/templates.md) for the full template list.
- See [Troubleshooting](../guide/troubleshooting.md) for runtime diagnostics.
