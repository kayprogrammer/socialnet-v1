from django.conf import settings
import websockets
import json


def get_notification_message(obj):
    """This function returns a notification message"""
    ntype = obj.ntype
    message = f"{obj.sender.full_name} reacted to your post"
    if ntype == "REACTION":
        if obj.comment_id:
            message = f"{obj.sender.full_name} reacted to your comment"
        elif obj.reply_id:
            message = f"{obj.sender.full_name} reacted to your reply"
    elif ntype == "COMMENT":
        message = f"{obj.sender.full_name} commented on your post"
    elif ntype == "REPLY":
        message = f"{obj.sender.full_name} replied your comment"
    return message


async def sort_notification_slugs(notification):
    if notification.post:
        notification.post_slug = notification.post.slug
    elif notification.comment:
        notification.comment_slug = notification.comment.slug
        notification.post_slug = notification.comment.post.slug
    elif notification.reply:
        notification.reply_slug = notification.reply.slug
        notification.comment_slug = notification.reply.comment.slug
        notification.post_slug = notification.reply.comment.post.slug
    return notification


# Send notification in websocket
async def send_notification_in_socket(
    secured: bool, host: str, notification: object, status: str = "CREATED"
):
    websocket_scheme = "wss://" if secured else "ws://"
    uri = f"{websocket_scheme}{host}/api/v1/ws/notifications/"
    notification_data = {"id": notification.id, "status": status}
    if status == "CREATED":
        notification = await sort_notification_slugs(notification)

        from apps.profiles.serializers import NotificationSerializer

        notification_data = NotificationSerializer(notification).data | {
            "status": status
        }

    headers = [
        ("Authorization", settings.SOCKET_SECRET),
    ]
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # Send a notification to the WebSocket server
        await websocket.send(json.dumps(notification_data))
        await websocket.close()
