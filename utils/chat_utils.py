from dependencies import (
    get_anthropic_client, get_openai_client, get_assistant_id
)
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

assistant_id = get_assistant_id()
openai_client = get_openai_client()
anthropic_client = get_anthropic_client()

class Message(BaseModel):
    """ Class to represent a message. """
    role: str = Field("user", description="The role of the message.")
    content: str = Field(..., description="The content of the message.")
    file_ids: List[str] = Field([], description="The file IDs of the message.")

def upload_openai_file(file: bytes) -> str:
    """ Upload a file to OpenAI. 
    Expects a base64 encoded file. """
    file = openai_client.create(
        file = open(file, "rb"),
        purpose = "assistants"
    )
    return file.id

def create_message(content: str, file_ids: List[str] = None) -> Message:
    """ Create a message to send to the assistant. """
    return Message(
        role = "user",
        content = content,
        file_ids = file_ids if file_ids else []
    )

def add_message_to_thread(message: Message, thread_id: str) -> str:
    """ Add a message to an existing thread. """
    thread_message = openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        role=message.role,
        content=message.content,
        file_ids=message.file_ids if message.file_ids else []
    )

    return thread_message.id

def create_run(message_content: str, file_ids: Optional[List[str]] = None, thread_id: Optional[str] = None):
    """ Create a thread in the assistant. """
    # If there is no thread ID, create a new thread and run
    if thread_id is None:
        logger.info("Creating new thread")
        run = openai_client.beta.threads.runs.create_and_run(
            assistant_id=assistant_id,
            thread={
                "messages" : [
                    {
                        "role": "user",
                        "content": message_content,
                        "file_ids": file_ids if file_ids else []
                    }
                ]
            }
        )

        return {"run_id": run.id, "thread_id": run.thread_id}

    else:
        # Add the message to the existing thread
        message = create_message(message_content, file_ids)
        logger.info(f"Adding message {message} to thread {thread_id}")
        message_id = add_message_to_thread(message, thread_id)
        logger.info(f"Message {message_id} added to thread {thread_id}")
        run = openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        return {"run_id": run.id, "thread_id": run.thread_id}