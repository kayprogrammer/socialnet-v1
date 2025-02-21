from django.conf import settings
import time
import cloudinary
import cloudinary.uploader
import mimetypes

BASE_FOLDER = "socialnet-v1/"

# FILES CONFIG WITH CLOUDINARY
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


class FileProcessor:
    @staticmethod
    def generate_file_signature(key, folder):
        key = f"{BASE_FOLDER}{folder}/{key}"
        timestamp = str(int(time.time()))
        params = {
            "public_id": key,
            "timestamp": timestamp,
        }
        try:
            signature = cloudinary.utils.api_sign_request(
                params_to_sign=params, api_secret=settings.CLOUDINARY_API_SECRET
            )
            return {"public_id": key, "signature": signature, "timestamp": timestamp}
        except Exception as e:
            print(e)
            pass

    def generate_file_url(key, folder, content_type):
        file_extension = mimetypes.guess_extension(content_type)
        key = f"{BASE_FOLDER}{folder}/{key}{file_extension}"

        try:
            return cloudinary.utils.cloudinary_url(key, secure=True)[0]
        except Exception as e:
            print(e)
            pass

    def upload_file(file, key, folder):
        key = f"{BASE_FOLDER}{folder}/{key}"
        try:
            cloudinary.uploader.upload(file, public_id=key, overwrite=True, faces=True)
        except Exception as e:
            print(e)
            pass
