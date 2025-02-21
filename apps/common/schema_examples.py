file_upload_data = {
    "public_id": "d23dde64-a242-4ed0-bd75-4c759624b3a6",
    "signature": "djsdsjAushsh",
    "timestamp": "16272637829",
}

user_data = {"name": "John Doe", "slug": "john-doe", "avatar": "https://img.url"}

latest_message_data = {
    "sender": user_data,
    "text": "Cool text",
    "file": "https://img.url",
}

notification_data = {
    "sender": user_data,
    "ntype": "REACTION",
    "post_slug": "john-doe-d23dde64-a242-4ed0-bd75-4c759624b3a6",
    "comment_slug": "john-doe-a23dde64-a242-4ed0-bd75-4c759624b3a9",
    "reply_slug": "john-doe-a45dde64-a242-4ed0-bd75-4c759624b3a1",
    "message": "John Doe reacted to your post",
    "is_read": False,
}
