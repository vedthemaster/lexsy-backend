import asyncio
import json

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from config import config

class OpenAIHandler:
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        
    async def create_thread(self):
        thread = await self.client.beta.threads.create()
        return thread.id
    
    async def _upload_file(self, document: str) -> str:
        with open(document, "rb") as file:
            file = await self.client.files.create(file=file, purpose="assistants")

        return file.id
    
    async def find_placeholders(self, thread_id: str, assistant_id: str, file_path: str):
        # Upload the file
        file_id = await self._upload_file(file_path)
        
        # Add message with file attachment to thread
        await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content="find the placeholders in the document",
            attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]}]
        )
        
        # Run the assistant with structured output
        run = await self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        
        placeholders = []
        
        if run.status == "completed":
            print("Run completed successfully.")
            pass
        
        elif run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                tool_id = tool_call.id
                
            if function_name == "extract_placeholders":
                    if not placeholders:
                        placeholders = json.loads(tool_call.function.arguments)
                    
            tool_outputs.append({
                "tool_call_id": tool_id,
                "output": "Done"
            })
            
            new_run = await self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                tool_outputs=tool_outputs,
                run_id=run.id
            )
            
        print("Extracted Placeholders:",placeholders)
            
        
        
        # # Wait for completion
        # while run.status in ["queued", "in_progress"]:
        #     run = await self.client.beta.threads.runs.retrieve(
        #         thread_id=thread_id,
        #         run_id=run.id
        #     )
        #     await asyncio.sleep(0.5)
        
        # # Get the response
        messages = await self.client.beta.threads.messages.list(thread_id=thread_id)
        response_text = messages.data[0].content[0].text.value
        
        return response_text
    
async def main():
    handler = OpenAIHandler()
    thread_id = await handler.create_thread()
    
    result = await handler.find_placeholders(
        thread_id=thread_id,
        assistant_id="asst_tY9imyJOBLa2vizzFcbEpPHG",  # Replace with your assistant ID
        file_path="resume.docx"
    )
    
    print("Result:", result)
    
if __name__ == "__main__":
    asyncio.run(main())
    
          

# client = OpenAI(api_key=config.OPENAI_API_KEY)

# class Placeholders(BaseModel):
#     names: list[str]

# response = client.chat.completions.parse(
#     model="gpt-4o-mini",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant that extracts placeholders from documents."},
#         {"role": "user", "content": "find the placeholders in the document"},
#     ],
#     response_format=Placeholders,
#     attachments=[{"file_id": "file-Fn9oU1K2hc66KtYy7c4x5C", "tools": [{"type": "file_search"}]}]
    
# )

# placeholders = response.output_parsed
# print("Extracted Placeholders:", placeholders.names)