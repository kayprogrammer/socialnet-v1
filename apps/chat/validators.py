from django.core.exceptions import ValidationError


def validate_chat_users_m2m(users, ctype, owner):
    users_count = users.count()
    if users_count > 1 and ctype == "DM":
        raise ValidationError("You can't assign more than 1 user")
    elif owner in users.all():
        raise ValidationError("Owner cannot be in users")
    elif users_count > 99:  # Group owner is one
        raise ValidationError("Cannot have more than 100 users in a group")
