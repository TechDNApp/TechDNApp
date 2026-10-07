import os
from .base import * 

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]