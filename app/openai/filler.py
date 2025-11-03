import asyncio
import json

from openai import AsyncOpenAI
from pydantic import BaseModel

from config import config
from repository import document_repo_ins


class OpenAIFiller:

    def __init__(self, document_id: str):
        self.document_id: str = document_id
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.assistant_id = config.OPENAI_FILLER_ASSISTANT_ID

    async def create_thread_and_start_conversation(self):
        """
        Create thread, upload document, send placeholder data, and start conversation
        Returns thread_id and initial conversation
        """
        document = await document_repo_ins.get_document_by_id(self.document_id)

        if not document:
            raise ValueError(f"Document with id {self.document_id} not found")

        thread = await self.client.beta.threads.create()
        thread_id = thread.id

        file_id = await self._upload_file(document.path)

        placeholders_data = []
        for ph in document.placeholders:
            placeholders_data.append(
                {
                    "name": ph.name,
                    "placeholder": ph.placeholder,
                    "regex": ph.regex,
                    "current_value": ph.value if ph.value else "Not filled yet",
                }
            )

        initial_message = f"""Document Title: {document.title}

Placeholders to fill:
{json.dumps(placeholders_data, indent=2)}

Please start by asking the user for the value of the FIRST placeholder. Ask one placeholder at a time in a friendly, conversational manner. After the user provides a value, use the save_placeholder function to save it, then move to the next placeholder."""

        await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=initial_message,
            attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]}],
        )

        run = await self.client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=self.assistant_id
        )

        await self._wait_for_run_completion(thread_id, run.id)

        conversation = await self.get_conversation_history(thread_id)

        return {
            "thread_id": thread_id,
            "conversation": conversation,
            "all_filled": await self._check_all_filled(),
        }

    async def process_user_message(self, thread_id: str, user_message: str):
        """
        Process user's response, save placeholder if needed, and continue conversation
        Returns updated conversation history
        """
        await self.client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=user_message
        )

        run = await self.client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=self.assistant_id
        )

        await self._wait_for_run_completion(thread_id, run.id)

        conversation = await self.get_conversation_history(thread_id)

        all_filled = await self._check_all_filled()

        return {"conversation": conversation, "all_filled": all_filled}

    async def _wait_for_run_completion(self, thread_id: str, run_id: str):
        """Wait for run to complete and handle function calls"""
        while True:
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run_id
            )

            if run.status == "completed":
                break
            elif run.status == "requires_action":
                # Handle function calls
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    if tool_call.function.name == "save_placeholder":
                        # Parse function arguments
                        arguments = json.loads(tool_call.function.arguments)
                        placeholder_name = arguments["placeholder_name"]
                        value = arguments["value"]

                        # Save placeholder value
                        success = await self._save_placeholder_value(
                            placeholder_name, value
                        )

                        result_message = (
                            f"Successfully saved '{value}' for placeholder '{placeholder_name}. Now you can ask for the next placeholder.'"
                            if success
                            else f"Failed to save placeholder '{placeholder_name}'"
                        )

                        tool_outputs.append(
                            {"tool_call_id": tool_call.id, "output": result_message}
                        )

                # Submit tool outputs
                run = await self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs
                )
            elif run.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed with status: {run.status}")

            await asyncio.sleep(0.5)

    async def _save_placeholder_value(self, placeholder_name: str, value: str) -> bool:
        """Save placeholder value to database"""
        try:
            document = await document_repo_ins.get_document_by_id(self.document_id)

            if not document:
                return False

            for placeholder in document.placeholders:
                if placeholder.name == placeholder_name:
                    placeholder.value = value
                    break

            await document_repo_ins.update_document(self.document_id, document)

            return True
        except Exception as e:
            print(f"Error saving placeholder: {e}")
            return False

    async def _check_all_filled(self) -> bool:
        """Check if all placeholders have values"""
        try:
            document = await document_repo_ins.get_document_by_id(self.document_id)

            if not document:
                return False

            for placeholder in document.placeholders:
                if not placeholder.value:
                    return False

            return True
        except Exception as e:
            print(f"Error checking placeholders: {e}")
            return False

    async def get_conversation_history(self, thread_id: str):
        """Get full conversation history as JSON"""
        messages = await self.client.beta.threads.messages.list(
            thread_id=thread_id, order="asc"
        )

        conversation = []
        for message in messages.data:
            conversation.append(
                {
                    "role": message.role,
                    "content": message.content[0].text.value if message.content else "",
                    "timestamp": message.created_at,
                }
            )

        return conversation

    async def _upload_file(self, document_path: str) -> str:
        """Upload document file to OpenAI"""
        with open(document_path, "rb") as file:
            file_obj = await self.client.files.create(file=file, purpose="assistants")
        return file_obj.id
