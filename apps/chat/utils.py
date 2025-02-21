from django.db.models import Q
from apps.accounts.models import User
from apps.common.error import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.models import File
from asgiref.sync import sync_to_async


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


def get_user(user):
    return {
        "name": user.full_name,
        "username": user.username,
        "avatar": user.get_avatar,
    }


async def usernames_to_add_and_remove_validations(
    chat, usernames_to_add=None, usernames_to_remove=None
):
    original_existing_user_ids = await sync_to_async(list)(
        chat.users.values_list("id", flat=True)
    )
    expected_user_total = len(original_existing_user_ids)
    users_to_add = []
    if usernames_to_add:
        users_to_add = await sync_to_async(list)(
            User.objects.filter(username__in=usernames_to_add).exclude(
                Q(id__in=original_existing_user_ids) | Q(id=chat.owner_id)
            )
        )
        expected_user_total += len(users_to_add)
    users_to_remove = []
    if usernames_to_remove:
        if not original_existing_user_ids:
            raise RequestError(
                err_code=ErrorCode.INVALID_ENTRY,
                err_msg="Invalid Entry",
                status_code=422,
                data={"usernames_to_remove": "No users to remove"},
            )
        users_to_remove = await sync_to_async(list)(
            User.objects.filter(
                username__in=usernames_to_remove, id__in=original_existing_user_ids
            ).exclude(id=chat.owner_id)
        )
        expected_user_total -= len(users_to_remove)

    if expected_user_total > 99:
        raise RequestError(
            err_code=ErrorCode.INVALID_ENTRY,
            err_msg="Invalid Entry",
            status_code=422,
            data={"usernames_to_add": "99 users limit reached"},
        )

    if users_to_add:
        await sync_to_async(update_group_chat_users)(chat, "add", users_to_add)
    if users_to_remove:
        await sync_to_async(update_group_chat_users)(chat, "remove", users_to_remove)
    return chat
