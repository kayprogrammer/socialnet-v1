from apps.common.models import File


async def create_file(file_type=None):
    file = None
    if file_type:
        file = await File.objects.acreate(resource_type=file_type)
    return file


async def sort_users_entry(users_entry: list):
    add_usernames = []
    remove_usernames = []
    for user in users_entry:
        if user["action"] == "ADD":
            add_usernames.append(user["username"])
        else:
            remove_usernames.append(user["username"])
    return add_usernames, remove_usernames
