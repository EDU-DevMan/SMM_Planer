import os

from dotenv import load_dotenv
from ok_api import OkApi

load_dotenv()

OK_ACCESS_TOKEN = os.environ.get("OK_ACCESS_TOKEN")
OK_PUBLIC_KEY = os.environ.get("OK_PUBLIC_KEY")
OK_SECRET_KEY = os.environ.get("OK_SESSION_SECRET")
OK_GROUP_ID = os.environ.get("OK_GROUP_ID")
ok_access = OkApi(
    access_token=OK_ACCESS_TOKEN,
    application_key=OK_PUBLIC_KEY,
    application_secret_key=OK_SECRET_KEY
)