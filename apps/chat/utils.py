from apps.common.models import File


async def create_file(file_type=None):
    file = None
    if file_type:
        file = await File.objects.acreate(resource_type=file_type)
    return file


def update_group_chat_users(instance, action, data):
    if len(data) > 0:
        if action == "add":
            instance.users.add(*data)
        elif action == "remove":
            instance.users.remove(*data)
        else:
            raise ValueError("Invalid Action")


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
