# Nada
## Not Another Diminutive Agent
A distributed async agent orchestration system built with Docker, Python, FastAPI, Pydantic AI, and Celery. Essentially a research project, and absolutely not ready for prime time. Here nonetheless as it might be helpful to others who are interested in evaluating (in particular) open source LLMs, agent frameworks, and LLM orchestration/performance. At the moment, only OpenAI compatible (Llama.cpp, Ollama, etc.) providers, along with Openrouter are supported.

## 🚀 Overview
The problem: How to best (or at least, not worst) break multi-step workflows into discrete steps, with repeatability and full audit along the way, and employing the minimal toolset for each step. How do we add checkpoints, and make use of the right LLM for the job? And how might this be accomplished without the risks and potential costs of something like an iterative ReAct loop? Linear regression machines (like LLMs) for any problem with a relatively long horizon carry substantial risks of error amplification downstream, combined with a complete inability to self-correct along the way. How do we find a balance? Let's find out. 

Essentially a fork (with gratitude!) of https://github.com/blairhudson/fastapi-agents, repurposed as an agent and LLM orchestration tool. Built to provide a sufficiently powerful agent that is not confined to either a console or an IDE, and that can offload long-running workloads to a lightweight async worker pool. More capabilities are coming (soon) with truly async execution, multi-step planning, Redis for cache, memory, and semantic search, as well as comprehensive LLM/agent metrics.    

Nada is a framework for building and managing AI agents that can interact with FastAPI applications and perform various tasks including web search, file system operations, and API calls (so far), using the Pydantic AI capabilities system.

Basically a test harness at this point, built to test the proposition that the app could then be used to generate usable code for itself. And to benchmark results and performance for various (small-ish) open source models, for actual day-to-day development work. Certain pieces, including this document, are the work of Qwen3.5 4B running on an old laptop. Totally sufficient for many tasks and agent tools, IMHO.

## 📋 Features

- **AI Agent Orchestration**: Built-in support for Pydantic AI and FastAPI integration
- **Distributed Task Processing**: Celery-based async task queue with Redis support
- **FastAPI Integration**: Seamless API interaction with AI agents
- **Multiple LLM Providers**: Support for local Llama models (via OpenAI-compatible APIs), OpenRouter, and more
- **Tool Integration**: Web search, file system access, shell execution, task planning, Telegram notifications
- **Model Management**: Dynamic model loading/unloading with provider support
- **Chat Interface**: Built-in web UI for agent interaction (agent-generated and original)
- **Redis Integration**: Redis-backed session management, caching, and Lua script support
- **API Discovery**: Automatic FastAPI route discovery and documentation for agent context
- **User Authentication**: JWT-based authentication with password hashing

## 🏗️ Project Structure

```
nada/
├── __init__.py              # Package initialization (PARENT_DIR_PATH, ROOT_DIR_PATH)
├── main.py                  # FastAPI application entry point
├── deps.py                  # Dependency injection (Redis, Agent, Providers)
├── models.py                # Pydantic model definitions
├── settings.py              # Application settings (env-based)
├── security.py              # Security utilities (JWT, password hashing)
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
│       ├── static/
│       │   ├── index.html
│       │   ├── chat.js
│       │   ├── script.js
│       │   ├── styles.css
│       │   └── new_style.css
│       └── templates/
│           ├── base.html
│           ├── index.html
│           └── login.html
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
    ├── planner.py           # Task planning tools
    └── telegram.py          # Telegram notification tool
```

## 🛠️ Requirements

- Python 3.11+
- Redis (for Celery, caching, and session management)

### Core Dependencies

- Celery 5.6.3+
- Gevent 26.5.0+
- Redis 8.0.0+
- Dogpile.cache 1.5.0+
- python-dotenv 0.9.9+
- pydantic-ai-slim[openai,openrouter,duckduckgo,web-fetch,mcp] 2.9.0+
- pydantic-ai-harness 0.6.0+
- FastAPI 0.139.0+
- Jinja2 3.1.6+
- python-magic 0.4.0+
- markitdown 0.1.6+
- PyJWT 1.4.0+
- bcrypt 5.0.0+
- python-slugify 8.0.4+
- pwdlib[argon2] 0.3.1+

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

### Docker Setup

Build the Docker image:

```bash
docker build -t nada .
```

Or use Docker Compose:

```bash
docker compose -f container-compose.yml up
```

### Creating Users

After installation, you can create users using the included script. See [CREATE_USER.md](./CREATE_USER.md) for detailed instructions.

```bash
# Interactive mode
python -m nada.scripts.user.create_users

# From a JSON file
python -m nada.scripts.user.create_users --path users.json
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root (one level above `nada/`):

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

### Provider Configuration

Create a `providers.json` file (path configured via `PROVIDER_CONFIG_PATH`) with LLM provider definitions:

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

### Docker Compose Configuration

The `container-compose.yml` defines three services:

1. **celery-worker-pool** - Celery worker with gevent pool
2. **fastapi_agent** - FastAPI application with chat UI
3. **redis-db** - Redis database with ACL-based authentication

Required environment variables for Docker Compose:

```env
# Redis connection
REDIS_DATA_HOST=redis-db
REDIS_DATA_PORT=6389
REDIS_DATA_DBNUM=
REDIS_DATA_USER=nada_data
REDIS_DATA_PASSWORD=changethis123

REDIS_CACHE_HOST=redis-db
REDIS_CACHE_PORT=6389
REDIS_CACHE_DBNUM=
REDIS_CACHE_USER=nada_data
REDIS_CACHE_PASSWORD=changethis123

CELERY_REDIS_USER=
CELERY_REDIS_PASSWORD=

# LLM provider
PROVIDER_DEFAULT=
PROVIDER_MODEL_DEFAULT=
OPENROUTER_API_KEY=

# Paths
NADA_HOME_DEFAULT=
NADA_GLOBAL_READ=
REDIS_PERSIST_DIR=

# Optional
DB_CONNECTION_URI=
APP_DB_CONNECTION_URI=
GH_TOKEN=
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

Install a Python venv with the project dependencies and update LLM provider configuration (in `providers.json` and `.env`). Then:

```bash
uvicorn nada.main:app --host 0.0.0.0 --port 8000
```

Or using the Docker Compose setup:

```bash
docker compose -f container-compose.yml up
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
