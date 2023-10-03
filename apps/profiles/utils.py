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
