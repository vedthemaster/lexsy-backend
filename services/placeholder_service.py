from app.openai import OpenAIFiller


class PlaceholderService:

    async def start_filling_session(self, document_id: str):
        """
        Start a new conversation session for filling placeholders
        Returns thread_id and initial conversation
        """
        filler = OpenAIFiller(document_id)
        result = await filler.create_thread_and_start_conversation()

        return result

    async def continue_conversation(
        self, document_id: str, thread_id: str, user_message: str
    ):
        """
        Continue the conversation with user's response
        Returns updated conversation and completion status
        """
        filler = OpenAIFiller(document_id)
        result = await filler.process_user_message(thread_id, user_message)

        return result


placeholder_service = PlaceholderService()
