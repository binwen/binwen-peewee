import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True

INSTALLED_APPS = [
    "vip"
]

MIDDLEWARE = [
    'binwen.middleware.ServiceLogMiddleware',
    'binwen.middleware.RpcErrorMiddleware',
    'peeweext.binwen.PeeweeExtMiddleware'
]


