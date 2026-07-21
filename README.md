# Nada

A distributed async agent orchestration system built with Docker, Python, FastAPI, Pydantic AI, and Celery.

## 🚀 Overview
Essentially a fork of https://github.com/blairhudson/fastapi-agents, repurposed as an agent and LLM orchestration tool (soon) with async capabilities, multi-step planning, Redis for cache, memory, and semantic search, as well as comprehensive LLM/agent metrics. Built to provide a sufficiently powerful agent that is not confined to either a console or an IDE, and that can offload long-running workloads to an efficient async worker pool.    

Nada is a framework for building and managing AI agents that can interact with FastAPI applications and perform various tasks including web search, file system operations, and API calls (so far), using the Pydantic AI capabilities system. 

Basically a test harness at this point, built to test the proposition that the app could then be used to generate usable frontend code for itself. And to benchmark results and performance for various (small-ish) open source models, for actual day-to-day development work. Certain pieces, including this document, are the work of Qwen3.5 4B running on an old laptop. Totally suficient for many tasks and agent tools, IMHO.

## 📋 Features

- **AI Agent Orchestration**: Built-in support for Pydantic AI and FastAPI integration
- **Distributed Task Processing**: Celery-based async task queue with Redis support
- **FastAPI Integration**: Seamless API interaction with AI agents
- **Multiple LLM Providers**: Support for local Llama models, OpenRouter, and more
- **Tool Integration**: Web search, file system access, shell execution
- **Model Management**: Dynamic model loading/unloading with provider support
- **Chat Interface**: Built-in web UI for agent interaction

## 🏗️ Project Structure

```
nada/
├── __init__.py              # Package initialization
├── fastapi_agent/           # FastAPI agent integration
│   ├── __init__.py
│   ├── fastapi_agent.py     # Main FastAPI agent class
│   ├── fastapi_app.py       # FastAPI application setup
│   ├── fastapi_auth.py      # Authentication middleware
│   ├── fastapi_discovery.py # API route discovery
│   └── agents/
│       ├── __init__.py
│       ├── base_agent.py    # Base agent class
│       └── pydantic_ai.py   # Pydantic AI agent implementation
├── llm/                     # LLM integration
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   └── provider.py      # LLM provider abstraction
│   ├── locals.py            # Local Llama models
│   └── openrouter.py        # OpenRouter integration
├── nada_celery/             # Celery task integration
│   ├── __init__.py
│   ├── celery.py            # Celery app configuration
│   └── tasks.py             # Task definitions
├── redis.py                 # Redis client configuration
├── settings.py              # Application settings
├── models.py                # Model definitions
├── simple_agent.py          # Standalone agent example
└── tools/                   # Tool implementations
    ├── __init__.py
    └── planner.py           # Task planning tools
```

## 🛠️ Requirements

- Python 3.11+
- Redis (for Celery and caching)
- FastAPI 0.139.0+
- Celery 5.6.3+
- Pydantic AI 2.9.0+
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
If there were any actual tests (there are not), like so:
```bash
pip install -e ".[dev]"
```

### Docker

```bash
docker build -t nada .
docker run -p 8000:8000 nada
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
```

## 🎯 Usage

### Running the Simple Agent

```bash
python -m nada.simple_agent
```

This starts an interactive agent session with:
- Local Llama models (if available)
- Web search capabilities
- File system access
- Shell execution

### Running with FastAPI

```python
from fastapi import FastAPI
from nada.fastapi_agent.fastapi_agent import FastAPIAgent

app = FastAPI()
agent = FastAPIAgent(app, base_url="http://localhost:8000")

# Start the agent
uvicorn app:app --reload
```

Access the chat interface at: `http://localhost:8000/agent/chat`

## 🌐 API Endpoints

The FastAPI agent provides the following endpoints:

- `POST /agent/query` - Ask the AI agent about API endpoints
- `GET /agent/chat` - Web chat interface
- `POST /agent/models_update` - Update the model provider

## 🧪 Testing

```bash
pytest -v --cov=nada
```

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

1. **Model not loading**: Check that your local Llama server is running on the specified port
2. **Redis connection errors**: Verify Redis is running and accessible
3. **Permission errors**: Ensure proper permissions on the data directory

### Debug Mode

Set `debug=True` when initializing the FastAPI agent to see detailed logs.

## 📄 License

MIT License

## 👤 Author

Richard Rosenberg <richard-rosenberg@pollosalvaje.com>

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Note**: This is a beta project. Some features may change in future releases.
