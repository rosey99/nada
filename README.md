# Nada
## Not Another Diminutive Agent
A distributed async agent orchestration system built with Docker, Python, FastAPI, Pydantic AI, and Celery. Essentially a research project, and absolutely not ready for prime time. Here nonetheless as it might be helpful to others who are interested in evaluating (in particular) open source LLMs, agent frameworks, and LLM orchestration/performance. At the moment, only OpenAI compatible (Llama.cpp, Ollama, etc.) providers, along with Openrouter are supported.

## 🚀 Overview
Essentially a fork (with gratitude!) of https://github.com/blairhudson/fastapi-agents, repurposed as an agent and LLM orchestration tool. Built to provide a sufficiently powerful agent that is not confined to either a console or an IDE, and that can offload long-running workloads to a lightweight async worker pool. More capabilities are coming (soon) with truly async execution, multi-step planning, Redis for cache, memory, and semantic search, as well as comprehensive LLM/agent metrics.    

Nada is a framework for building and managing AI agents that can interact with FastAPI applications and perform various tasks including web search, file system operations, and API calls (so far), using the Pydantic AI capabilities system. 

Basically a test harness at this point, built to test the proposition that the app could then be used to generate usable code for itself. And to benchmark results and performance for various (small-ish) open source models, for actual day-to-day development work. Certain pieces, including this document, are the work of Qwen3.5 4B running on an old laptop. Totally sufficient for many tasks and agent tools, IMHO.


## 📋 Features

- **AI Agent Orchestration**: Built-in support for Pydantic AI and FastAPI integration
- **Distributed Task Processing**: Celery-based async task queue with Redis support (roadmap)
- **FastAPI Integration**: Seamless API interaction with AI agents
- **Multiple LLM Providers**: Support for local Llama models (via OpenAI-compatible APIs), OpenRouter, and more
- **Tool Integration**: Web search, file system access, shell execution, task planning, Telegram notifications
- **Model Management**: Dynamic model loading/unloading with provider support
- **Chat Interface**: Built-in web UI for agent interaction (agent-generated and original)
- **Redis Integration**: Redis-backed session management, caching, and Lua script support
- **API Discovery**: Automatic FastAPI route discovery and documentation for agent context

## 🏗️ Project Structure

```
nada/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application entry point
├── deps.py                  # Dependency injection (Redis, Agent, Providers)
├── models.py                # Pydantic model definitions
├── settings.py              # Application settings (env-based)
├── simple_agent.py          # Standalone interactive agent example
├── celery/                  # Celery task integration
│   ├── __init__.py
│   ├── celery.py            # Celery app configuration
│   └── tasks.py             # Task definitions
├── fastapi_agent/           # FastAPI agent integration
│   ├── __init__.py
│   ├── fastapi_agent.py     # Main FastAPI agent class
│   ├── fastapi_auth.py      # Authentication middleware
│   ├── fastapi_discovery.py # API route discovery
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py    # Base agent class (ABC)
│   │   └── pydantic_ai.py   # Pydantic AI agent implementation
│   └── chat_ui/             # Web chat interface
│       ├── index.html
│       ├── chat.js
│       ├── script.js
│       ├── styles.css
│       ├── new_style.css
│       └── templates/
│           └── index.html
├── llm/                     # LLM integration
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   └── provider.py      # LLM provider abstraction
│   ├── openai_compat.py     # OpenAI-compatible (Llama.cpp, Ollama) providers
│   └── openrouter.py        # OpenRouter integration
├── redis/                   # Redis client configuration
│   ├── __init__.py
│   ├── client/
│   │   ├── __init__.py
│   │   ├── redis_cache.py   # Redis cache client
│   │   └── redis_data.py    # Redis data client
│   ├── load_lua_funcs.py    # Lua function loader
│   └── lua/
│       └── kv.lua           # Key-value Lua scripts
├── routes/                  # API route definitions
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   └── agent_routes.py  # Agent chat and query endpoints
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           └── api_routes.py # API v1 endpoints
└── tools/                   # Tool implementations
    ├── __init__.py
    ├── planner.py           # Task planning tools (roadmap)
    └── telegram.py          # Telegram notification tool (roadmap)
```

## 🛠️ Requirements

- Python 3.11+
- Redis (for Celery, caching, and session management)
- FastAPI 0.139.0+
- Celery 5.6.3+
- Pydantic AI 2.9.0+ (pydantic-ai-slim with openai, openrouter, duckduckgo, web-fetch, mcp extras)
- Gevent 26.5.0+

### Development Dependencies

- Ruff 0.9.0+ (code formatting)
- MyPy 1.15.0+ (type checking)
- Pytest 8.3.0+ (testing)
- pytest-asyncio 0.25.0+ (async testing)
- pytest-cov 6.0.0+ (coverage)
- pre-commit 4.1.0+ (linting hooks)

## 📦 Installation

### From Source

```bash
pip install -e .
```

### Development Setup

```bash
pip install -e ".[dev]"
```

## 🔧 Configuration

Create a `.env` file in the project root:

```env
# Celery Configuration
CELERY_RESULT_URI=redis://localhost:6379/0
CELERY_BROKER_URI=redis://localhost:6379/0

# Redis Cache Configuration
REDIS_CACHE_HOST=localhost
REDIS_CACHE_PORT=6379
REDIS_CACHE_DBNUM=1

# Redis Data Configuration
REDIS_DATA_HOST=localhost
REDIS_DATA_PORT=6379
REDIS_DATA_DBNUM=2

# LLM Provider Configuration
PROVIDER_CONFIG_PATH=providers.json
PROVIDER_DEFAULT=
PROVIDER_MODEL_DEFAULT=

# OpenRouter API Key (optional)
OPENROUTER_API_KEY=

# Telegram Notifications (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# SMTP Configuration (optional)
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=
SMTP_TLS=true
SMTP_SSL=false
SMTP_PORT=587
```

Additionally, create a `providers.json` file (path configured via `PROVIDER_CONFIG_PATH`) with LLM provider definitions:

```json
[
  {
    "name": "local_llama",
    "prompt_url": "http://localhost:8080/v1",
    "models_url": "http://localhost:8080/models",
    "load_url": "http://localhost:8080/load",
    "api_key": "NOT_A_REAL_KEY",
    "get_available_models": "nada.llm.openai_compat:get_available_llama_models",
    "get_model": "nada.llm.openai_compat:get_llama_model"
  },
  {
    "name": "openrouter",
    "status": "unknown",
    "is_active": false,
    "prompt_url": "https://openrouter.ai/api/v1",
    "models_url": "",
    "load_url": "",
    "api_key": "OPENROUTER_API_KEY",
    "get_available_models": "nada.llm.openrouter:get_available_openrouter_models",
    "get_model": "nada.llm.openrouter:get_openrouter_model"
  }
]
```

## 🎯 Usage

### Running the Simple Agent

```bash
python -m nada.simple_agent
```

This starts an interactive agent session with:
- Configured LLM providers (local models or OpenRouter)
- Web search capabilities (DuckDuckGo, web fetch)
- File system access
- Shell execution

### Running with FastAPI

Install a python venv with the project dependencies and update LLM provider configuration (in `providers.json` and `.env`). Then:

```bash
uvicorn nada.main:app --host 0.0.0.0 --port 8000
```

Or using the Docker Compose setup:

```bash
docker-compose -f container-compose.yml up
```

Access the chat interface at: `http://localhost:8000/agent/v1/chat`

## 🌐 API Endpoints

The FastAPI agent provides the following endpoints:

### Agent Routes (`/agent/v1`)

- `GET /agent/v1/chat` - Web chat interface (HTML)
- `POST /agent/v1/query` - Ask the AI agent about API endpoints (accepts query, history, and optional files)
- `POST /agent/v1/models_update` - Update the active model provider and model selection

### API Routes (`/api/v1`)

- `GET /api/v1/` - Welcome/root endpoint
- `GET /api/v1/providers` - Retrieve model providers and models as JSON

## 🧪 Testing

```bash
pytest -v --cov=nada
```

Tests are organized in:
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests (e.g., Redis KV store tests)

## 📝 Development

### Code Quality

```bash
# Format code
ruff check .

# Type checking
mypy nada/

# Run tests
pytest -v
```

### Pre-commit Hooks

```bash
pre-commit install
```

## 🐛 Troubleshooting

### Common Issues

1. **Model not loading**: Check that your local Llama server is running on the specified port and accessible via OpenAI-compatible API
2. **Redis connection errors**: Verify Redis is running and accessible on the configured host/port
3. **Provider not found**: Ensure `providers.json` exists at the path specified by `PROVIDER_CONFIG_PATH` and contains valid provider definitions
4. **Permission errors**: Ensure proper permissions on the data directory and SSH keys directory (`/nada/.ssh`)

### Debug Mode

Set `debug=True` when initializing the FastAPI agent to see detailed logs.

## 📄 License

MIT License

## 👤 Author

Richard Rosenberg <richard-rosenberg@pollosalvaje.com>

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Note**: This is an alpha project. Some features will change in future releases.
