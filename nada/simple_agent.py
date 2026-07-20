#import asyncio
import logging
#import os
import time

from prompt_toolkit import PromptSession
#from prompt_toolkit.patch_stdout import patch_stdout


from pydantic_ai import Agent

from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

from pydantic_ai_harness import Shell, FileSystem

from nada.llm.locals import get_available_llama_models, get_llama_model
from nada.llm.common.provider import ProviderCollection
from nada.llm.openrouter import get_openrouter_model, get_available_openrouter_models
#from nada.models import ModelProvider
from nada.settings import settings

# TODO move this inside settings or out to compose
# just to support corner-case where container host
# is also running an LLM server, llama.cpp, Ollama, etc.

LOCAL_PROVIDERS = [
    {'name': "Local Llama LTV",
     'prompt_url': "http://192.168.1.39:8080/v1",
     'models_url': "http://192.168.1.39:8080/models",
     'load_url': "http://192.168.1.39:8080/load",
     'support_autoload': True,
     'get_available_models': get_available_llama_models,
     'get_model': get_llama_model,
     'models_api_timeout': 5,
     },
     {'name': "Local Llama BSlow",
      'prompt_url': settings.HOST_LLM_SERVER + "/v1",
      'models_url': settings.HOST_LLM_SERVER + "/models",
      'load_url': settings.HOST_LLM_SERVER + "load",
      'support_autoload': True,
      'get_available_models': get_available_llama_models,
      'get_model': get_llama_model,
      'models_api_timeout': 5,
      },
      {'name': "Openrouter",
       'prompt_url': "https://openrouter.ai/api/v1",
       'models_url': "",
       'load_url': "",
       'support_autoload': True,
       'get_available_models': get_available_openrouter_models,
       'get_model': get_openrouter_model,
       'models_api_timeout': 5,
       'api_key': settings.OPENROUTER_API_KEY,
       },
]

# setup logging
logger = logging.getLogger(__name__)
#logging.basicConfig(filename='agent.log', encoding='utf-8', level=logging.DEBUG)

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
#     """Setup and run the interactive agent loop."""
    # Get providers, start with local
    providers = ProviderCollection(provider_list=LOCAL_PROVIDERS)

    # modifies in place and returns
    providers.refresh_provider()
    provider = providers.providers['Local Llama LTV']

    use_model = None
    for model in provider.models:
        # get the loaded model
        if model.model_status == 'loaded':
            use_model = get_llama_model(model_id=model.id, provider=provider)
            #print('Found loaded model: ', model.id, model.model_status)
            #print(f'Context: {model.context_size}')
    if not use_model:
        use_model = providers.get_model_obj(model_id='unsloth/Qwen3.5-4B-MTP-GGUF:Q8_0', provider_name=provider.name)

    model = use_model

    #t = tool_from_langchain(ShellTool())
    #t.description = "Execute one or more bash commands as a list of strings."

    agent = Agent(
        model,
        instructions='You are a helpful and concise assistant.',
        #capabilities=[Thinking(), WebSearch(local='duckduckgo')],
        tools = [duckduckgo_search_tool(), web_fetch_tool(max_content_length=None)],
        capabilities=[Shell(), FileSystem()],
        #model_settings=
    )

    print("Providers and models:")
    for provider_name, provider_obj in providers.providers.items():
        print(f'  Provider {provider_name} status is {provider_obj.status} and has {len(provider_obj.models)} models available.')
        #for model in provider.models:
        #    print(f'  {model.aliases[0] if model.aliases else model.id}')
    print()
    print(f"Loaded: <{model.model_name}> from provider <{provider.name}>.")
    print()
    print("\n🔧 Available tools:")
    for toolset in agent.toolsets:
        if hasattr(toolset, 'tools'):
            # print(f"{type(toolset.tools)} - {dir(toolset.tools)}:") # {tool.description[:80]}")
            for tool in toolset.tools.values():
                print(f"{tool.name} - {tool.description[:80]}")
        if hasattr(toolset, 'toolsets'):
            for tools in toolset.toolsets:
                start = '<summary>'
                print(tools.capability.get_instructions())
                for tool in tools.capability.get_toolset().tools.values():
                    idx1 = tool.description.find(start)
                    idx2 = tool.description.find('</summary>', idx1 + len(start))
                    if idx1 != -1 and idx2 != -1:
                        res = tool.description[idx1 + len(start):idx2]
                        #print(res)


                    print(f"{tool.name} - {res}")

                #print(f"{type(tools.capability.get_toolset())} - {dir(tools.capability.get_toolset())}:") # {tool.description[:80]}")
            #print(tool.name, tool.description)

    print("\n🌐 Agent is ready! Ask questions about the internet.")
    print("\nType 'ctrl-c', 'quit' or 'exit' to stop the agent.")
    print()

    session_start_time = time.time()
    # Main interaction loop
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
            #thinking_budget_tokens = int((len(user_input) * 2) + 200)
            # Process the query
            print("\n🤖 Agent thinking...")

            result = agent.run_sync(user_input) # , model_settings={"thinking_budget_tokens": thinking_budget_tokens})
            end_time = time.time()
            # Display response
            elapsed_time = end_time - start_time

            print("Agent: ", result.output)
            print()
            print("Usage: ", result.usage)
            print('Request time: {:.2f} seconds'.format(elapsed_time))

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
