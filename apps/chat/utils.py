from apps.common.models import File


async def create_file(file_type=None):
    file = None
    if file_type:
        file = await File.objects.acreate(resource_type=file_type)
    return file
