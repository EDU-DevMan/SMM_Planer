import os
import requests
import json
from ok_api import OkApi
from dotenv import load_dotenv

load_dotenv()

# Загружаем ключи
OK_ACCESS_TOKEN = os.environ.get("OK_ACCESS_TOKEN")
OK_PUBLIC_KEY = os.environ.get("OK_PUBLIC_KEY")
# Берем SESSION_SECRET для подписи, так как именно он работал у коллеги
OK_SECRET_FOR_SIG = os.environ.get("OK_SESSION_SECRET") 
OK_GROUP_ID = os.environ.get("OK_GROUP_ID")

# Инициализируем API с СЕССИОННЫМ секретом
ok_api = OkApi(
    access_token=OK_ACCESS_TOKEN,
    application_key=OK_PUBLIC_KEY,
    application_secret_key=OK_SECRET_FOR_SIG 
)


def upload_photo_to_ok(image_url):
    """Загружает фото и возвращает токен для публикации"""
    if not image_url or not image_url.startswith('http'):
        return None
    try:
        url_res = ok_api.photosV2.getUploadUrl(count=1, gid=OK_GROUP_ID).json()
        upload_url = url_res["upload_url"]
        
        img_data = requests.get(image_url).content
        files = {"photo": ("image.jpg", img_data)}
        
        upload_res = requests.post(upload_url, files=files).json()
        photo_id = list(upload_res["photos"].keys())[0]
        return upload_res["photos"][photo_id]["token"]
    except Exception as e:
        print(f"Ошибка загрузки фото в ОК: {e}")
        return None


def publish_to_ok(text, photo_url=None):
    """Публикует пост в ОК"""
    try:
        attachment = {"media": []}
        if text:
            attachment["media"].append({"type": "text", "text": text})
        
        if photo_url:
            photo_token = upload_photo_to_ok(photo_url)
            if photo_token:
                attachment["media"].append({"type": "photo", "list": [{"id": photo_token}]})

        # Публикация
        res = ok_api.mediatopic.post(
            type="GROUP_THEME",
            gid=OK_GROUP_ID,
            attachment=json.dumps(attachment)
        ).json()
        
        # ОК возвращает ID поста в виде строки
        if isinstance(res, str):
            return res
        return None
    except Exception as e:
        print(f"Ошибка публикации в ОК: {e}")
        return None


def delete_ok_post(topic_id):
    if not topic_id: return False
    try:
        response = ok_api.mediatopic.deleteTopic(topic_id=str(topic_id).strip())
        res_data = response.json()
        
        if res_data is True or (isinstance(res_data, dict) and res_data.get('success')):
            return True
        return False
    except Exception as e:
        return False