from .base import *

DEBUG = False
ASGI_PORT = config('PORT')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True