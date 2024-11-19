import asyncio
import tempfile

from autogen_core.application import SingleThreadedAgentRuntime
from autogen_ext.code_executors import DockerCommandLineCodeExecutor
from autogen_ext.models import OpenAIChatCompletionClient
from dataclasses import dataclass
from typing import List

from autogen_core.base import MessageContext
from autogen_core.components import DefaultTopicId, RoutedAgent, default_subscription, message_handler
from autogen_core.components.code_executor import CodeExecutor, extract_markdown_code_blocks
from autogen_core.components.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
)


@dataclass
class Message:
    content: str


@default_subscription
class Assistant(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("An assistant agent.")
        self._model_client = model_client
        self._chat_history: List[LLMMessage] = [
            SystemMessage(
                content="""Write Python script in markdown block, and it will be executed.
Always save figures to file in the current directory. Do not use plt.show()""",
            )
        ]

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        self._chat_history.append(UserMessage(content=message.content, source="user"))
        result = await self._model_client.create(self._chat_history)
        print(f"\n{'-' * 80}\nAssistant:\n{result.content}")
        self._chat_history.append(AssistantMessage(content=result.content, source="assistant"))  # type: ignore
        await self.publish_message(Message(content=result.content), DefaultTopicId())  # type: ignore


@default_subscription
class Executor(RoutedAgent):
    def __init__(self, code_executor: CodeExecutor) -> None:
        super().__init__("An executor agent.")
        self._code_executor = code_executor

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        code_blocks = extract_markdown_code_blocks(message.content)
        if code_blocks:
            result = await self._code_executor.execute_code_blocks(
                code_blocks, cancellation_token=ctx.cancellation_token
            )
            print(f"\n{'-' * 80}\nExecutor:\n{result.output}")
            await self.publish_message(Message(content=result.output), DefaultTopicId())


work_dir = tempfile.mkdtemp()

# Create an local embedded runtime.
runtime = SingleThreadedAgentRuntime()


async def main():
    # Initialize the DockerCommandLineCodeExecutor
    async with DockerCommandLineCodeExecutor(work_dir=work_dir) as executor:
        # Register the assistant agent with the runtime
        await Assistant.register(
            runtime,
            "assistant",
            lambda: Assistant(
                OpenAIChatCompletionClient(
                    model="gpt-4o",
                    api_key=""
                )
            ),
        )

        # Register the executor agent
        await Executor.register(runtime, "executor", lambda: Executor(executor))

        # Start the runtime and send a message
        runtime.start()
        await runtime.publish_message(
            Message("Create a plot of NVIDIA vs TSLA stock returns YTD from 2024-01-01."),
            DefaultTopicId()
        )

        # Stop the runtime when idle
        await runtime.stop_when_idle()


# Run the main function
asyncio.run(main())
