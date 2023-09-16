from django.core.exceptions import ValidationError


def validate_chat_users_m2m(users, ctype, owner):
    if users.count() > 1 and ctype == "DM":
        raise ValidationError("You can't assign more than 1 user")
    elif owner in users.all():
        raise ValidationError("Owner cannot be in users")
