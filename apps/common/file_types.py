ALLOWED_IMAGE_TYPES = [
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
    "image/svg+xml",
]

ALLOWED_AUDIO_TYPES = ["audio/mp3", "audio/aac", "audio/wav", "audio/m4a"]

ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "application/msword",
]

ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_AUDIO_TYPES + ALLOWED_DOCUMENT_TYPES
