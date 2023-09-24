from django.conf import settings
from uuid import UUID
from apps.common.file_processors import FileProcessor
from apps.common.models import File
import websockets
import json


# Create file object
async def create_file(file_type=None):
    file = None
    if file_type:
        file = await File.objects.acreate(resource_type=file_type)
    return file


# Update group chat users m2m
def update_group_chat_users(instance, action, data):
    if len(data) > 0:
        if action == "add":
            instance.users.add(*data)
        elif action == "remove":
            instance.users.remove(*data)
        else:
            raise ValueError("Invalid Action")


# Handle errors for users m2m
def handle_lerrors(err):
    errA = err.get("usernames_to_add")
    errR = err.get("usernames_to_remove")
    errors = {}
    if errA:
        if isinstance(errA, dict):
            first_key = list(errA)[0]
            errors["usernames_to_add"] = [errA[first_key][0]]

    if errR:
        if isinstance(errR, dict):
            first_key = list(errR)[0]
            errors["usernames_to_remove"] = [errR[first_key][0]]
    return errors


# Send message in websocket
async def send_message_in_socket(
    secured: bool, host: str, id: UUID, message: dict, status: str = "CREATED"
):
    websocket_scheme = "wss://" if secured else "ws://"
    uri = f"{websocket_scheme}{host}/api/v1/ws/chat/{id}/"

    # Convert file upload data to file url
    file_upload_data = message.pop("file_upload_data", None)
    if file_upload_data:
        file = message["file"]
        message["file"] = FileProcessor.generate_file_url(
            key=file.id,
            folder="messages",
            content_type=file.resource_type,
        )

    message = message | {"status": status} | {"key": settings.SOCKET_SECRET}

    async with websockets.connect(uri) as websocket:
        # Send a message to the WebSocket server
        message_to_send = json.dumps(message)
        await websocket.send(message_to_send)
        await websocket.close()
