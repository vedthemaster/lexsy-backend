import asyncio
import json

from openai import AsyncOpenAI
from pydantic import BaseModel

from config import config


class OpenAIParser:

    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

    async def create_thread(self):
        thread = await self.client.beta.threads.create()
        return thread.id

    async def _upload_file(self, document: str) -> str:
        with open(document, "rb") as file:
            file = await self.client.files.create(file=file, purpose="assistants")

        return file.id

    async def find_placeholders(
        self, thread_id: str, assistant_id: str, file_path: str
    ):

        file_id = await self._upload_file(file_path)

        await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content="find the placeholders in the document",
            attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]}],
        )

        run = await self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        placeholders = []

        if run.status == "completed":
            # If run completed without requiring action, document has no placeholders
            raise ValueError(
                "This document has no placeholders to fill. Please upload a document with placeholder text."
            )

        elif run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls

            # Check if there are multiple tool calls
            if len(tool_calls) > 1:
                raise ValueError(
                    "Multiple tool calls detected. Please try uploading the file again."
                )

            # Check if there's exactly one tool call
            if len(tool_calls) == 0:
                raise ValueError(
                    "No tool calls found. Please try uploading the file again."
                )

            tool_call = tool_calls[0]
            function_name = tool_call.function.name
            tool_id = tool_call.id

            print(f"Tool call: {function_name}, ID: {tool_id}")
            print(f"Arguments: {json.loads(tool_call.function.arguments)}")

            if function_name == "extract_placeholders":
                placeholders_data = json.loads(tool_call.function.arguments)
                if "placeholders" in placeholders_data:
                    placeholders = placeholders_data["placeholders"]
            else:
                raise ValueError(
                    f"Unexpected function name: {function_name}. Please try uploading the file again."
                )

            tool_outputs = [{"tool_call_id": tool_id, "output": "Done"}]

            new_run = await self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id, tool_outputs=tool_outputs, run_id=run.id
            )

            return (
                {"placeholders": placeholders} if placeholders else {"placeholders": []}
            )

        else:
            # Handle other run statuses (failed, expired, etc.)
            raise ValueError(
                f"Run status '{run.status}'. Please try uploading the file again."
            )
