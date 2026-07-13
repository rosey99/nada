import asyncio
import logging
import os
import time

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking, WebSearch

from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

from pydantic_ai.models import ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from pydantic_ai.ext.langchain import tool_from_langchain

from nada.llm.locals import get_available_llama_models, get_llama_model, ProviderCollection
from nada.models import ModelProvider

from yada.tools.shell import bash_shell, CommandCollection, ShellTool

#model_settings = OpenAIChatModelSettings({'reasoning': 'off'})

local_providers = [
    {'name': "Local LTV LLM",
     'prompt_url': "http://192.168.1.39:8080/v1",
     'models_url': "http://192.168.1.39:8080/models",
     'load_url': "http://192.168.1.39:8080/load",
     'support_autoload': True,
     'get_available_models': get_available_llama_models,
     'get_model': get_llama_model,
     },
     {'name': "Local SlowBig LLM",
      'prompt_url': "http://127.0.0.1:8080/v1",
      'models_url': "http://127.0.0.1:8080/models",
      'load_url': "http://127.0.0.1:8080/load",
      'support_autoload': True,
      'get_available_models': get_available_llama_models,
      'get_model': get_llama_model,
      },

]
providers = ProviderCollection(provider_list=local_providers)
#provider = ModelProvider(**local_providers[0])
# modifies in place and returns
providers.refresh_provider()
#get_available_llama_models(provider=provider)
provider = providers.providers['Local LTV LLM']
use_model = None
for model in provider.models:
    # get the loaded model
    if model.model_status == 'loaded':
        use_model = get_llama_model(model_id=model.id, provider=provider)
        print('Found loaded model: ', model.id, model.model_status)
        print(f'Context: {model.model_args.ctx_size}')
if not use_model:
    use_model = providers.get_model_obj(model_id='unsloth/gemma-4-E4B-it-GGUF:Q8_K_XL', provider_name=provider.name)
model = use_model

# model = OpenAIChatModel(
#     'unsloth/gemma-4-E4B-it-GGUF:Q8_K_XL',
#     #'Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-MTP-GGUF:Q8_0',
#     #'yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF:Q6_K',
#     #'s-batman/ornith-1.0-35B-NVFP4-MTP-GGUF:MTP',
#     #'unsloth/Qwen3.5-4B-MTP-GGUF:Q8_0',
#     #'unsloth/Qwen3.5-9B-MTP-GGUF:Q8_K_XL',
#     provider=OpenAIProvider(
#         base_url='http://192.168.1.39:8080/v1',
#         #base_url='http://127.0.0.1:8080/v1',
#         api_key='your-api-key',
#     ),
#     settings = ModelSettings(thinking=False)
# )

agent = Agent(
    model,
    # 'anthropic:claude-sonnet-4-6',
    instructions='You are a helpful and concise assistant.',
    #capabilities=[Thinking(), WebSearch(local='duckduckgo')],
    tools=[duckduckgo_search_tool(), web_fetch_tool(max_content_length=None), tool_from_langchain(ShellTool())],
    #model_settings=
)

# from yada.agent.agent import get_agent
# from yada.llm.locals import get_openai
# from yada.llm.openrouter import create_openrouter_llm ,get_openrouter_models, OpenRouterModelListArgs, OpenRouterModel
# from yada.mcp_client.client import async_get_mcp_client
# from yada.tools.web import visit_webpage, ddg_websearch
# from yada.tools.shell import bash_shell
# from yada.tools.files import get_file_tools

# setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='agent.log', encoding='utf-8', level=logging.DEBUG)

#LLM_BASE_URL = "http://127.0.0.1:8080/v1"
LLM_BASE_URL = os.getenv('DEFAULT_AGENT_LLM') or "http://192.168.1.39:8080/v1"

# TODO move this out to yaml or something
# MCP server configuration
MCP_SERVERS = {
    "langchain-docs": {
        "transport": "http",
        "url": "https://docs.langchain.com/mcp",
    },
}

# interactive shell
async def interactive_shell(prompt_str: str):
    """
    Like 'interactive_shell,' but doing things manual.
    """
    # Create Prompt.
    # TODO? Allows for extension/examination of prompt potentially
    # out of process. Think of a longish regex or something?
    # Prompts can potentially be quite large, leave this async for now
    session = PromptSession(prompt_str)

    # Run loop. Read text from stdin. TODO add multi-line
    # and prompt-toolkit correctly handles ctrl-c, langchain tools not so much
    # probably wants an explicit error/type here for exit - safer than None
    while True:
        try:
            result = await session.prompt_async()
            logger.info('Client: {result}')
        except (EOFError, KeyboardInterrupt):
            return None
        return result


#async def main() -> None:
def main() -> None:
#     """Run the interactive agent loop."""
#     # tools
#     base_tools = []
#     base_tools.append(ddg_websearch)
#     base_tools.append(visit_webpage)
#     # Lame!
#     base_tools.extend(get_file_tools(include_tools=None))
#     base_tools.append(bash_shell)
#     base_tools.extend(await async_get_mcp_client(mcp_servers=MCP_SERVERS))
#     # TODO openrouter hack until interactive session is updated
#     list_args = OpenRouterModelListArgs()
#     openmodels = get_openrouter_models(list_args).model_dump()
#     # A single LLM
#     # TODO went a little berserk with models as args, toneit sown and set to dict
#     #  with manual validation
#     #llm_model = OpenRouterModel(**openmodels['models'][0])
#     #llm = create_openrouter_llm(llm_model) #get_openai(LLM_BASE_URL)
#     llm = get_openai(LLM_BASE_URL)
#     # Get/create the agent
#     agent = get_agent(
#         model=llm,
#         tools=base_tools,
#         system_prompt="You are a helpful assistant",
#     )
#     # Display available tools
#     print("\n🔧 Available tools:")
#     for tool in base_tools:
#         # Some tools have loooong descriptions for
#         #  prompt injection, e.g., MCP client
#         print(f"  - {tool.name}: {tool.description[:80]}")
#     print()
#     print(f"There are currently {openmodels['count']} OpenRouter (free!) models available :)")
#     # Print welcome message
    print("\n🌐 Agent is ready! Ask questions about the internet.")
    print("\nType 'ctrl-c', 'quit' or 'exit' to stop the agent.")
    print()
    for provider_name, provider in providers.providers.items():
        print(f'Provider: {provider_name} has {len(provider.models)} models available.')
        for model in provider.models:
            print(f'  {model.aliases[0] if model.aliases else None}')
    session_start_time = time.time()
#     # Main interaction loop
    while True:
        try:
            user_input = input("You: ")
            #user_input = await interactive_shell("You: ")

            # Exit conditions
            if user_input is None or user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Agent stopped. Thanks for using it!")
                break

            if not user_input.strip():
                print("Please enter a question.\n")
                continue
            start_time = time.time()
            thinking_budget_tokens = int((len(user_input) * 2) + 200)
            # Process the query
            print("\n🤖 Agent thinking...")
#             response = agent.invoke(
#                 {"messages": [{"role": "user", "content": user_input, }],
#                  "thinking_budget_tokens": thinking_budget_tokens,
#                  # "reasoning_budget_start_tokens": 200,
#                  # "reasoning_budget_max_tokens": thinking_budget_tokens
#                  }
#             )
            result = agent.run_sync(user_input) # , model_settings={"thinking_budget_tokens": thinking_budget_tokens})
            end_time = time.time()
            # Display response
            elapsed_time = end_time - start_time
            print("Agent: ", result.output)
            print("Usage: ", result.usage)
            print('Request time: {:.2f} seconds'.format(elapsed_time))

#             for item in response["messages"]:
#                 if item.type == 'ai':
#                     # print(f"  role: {item.role}")
#                     # print(f"  name: {item.name}")
#                     print(f"  Agent: {item.content}")

        except KeyboardInterrupt:
            print("\n\n👋 Agent stopped. Thanks for using it!")
            break

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or check your local server.")

    session_end_time = time.time()
    session_elapsed_time = session_end_time - session_start_time
    print('Total session time {:2f} seconds'.format(session_elapsed_time))



if __name__ == "__main__":
    """
    For scripts/binary entry
    """
    # with patch_stdout():
    #     try:
    #         asyncio.run(main())
    #     except Exception as e:
    #         print(f'An error occured: {str(e)}')
    #         raise  # TODO re-raise for traceback
    #     finally:
    #         print('Shutting down. . .')
    # ayncio.run(main())
    try:
        main()
    except Exception as e:
        print(f'An error occured: {str(e)}')
        raise  # TODO re-raise for traceback
    finally:
        print('Shutting down. . .')
