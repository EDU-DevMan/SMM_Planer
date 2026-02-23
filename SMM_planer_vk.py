import os
import requests
from dotenv import load_dotenv

load_dotenv()

VK_USER_TOKEN = os.environ.get('VK_USER_TOKEN')
VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
VK_API_VERSION = '5.131'


def upload_photo_to_vk(image_url):
    """Загружает фото на сервера VK и возвращает attachment ID"""
    if not image_url or not image_url.startswith('http'):
        return None

    try:
        # 1. Получаем адрес сервера для загрузки
        method_url = "https://api.vk.com/method/photos.getWallUploadServer"
        params = {
            "group_id": VK_GROUP_ID.replace('-', ''), # ID группы без минуса
            "access_token": VK_USER_TOKEN,
            "v": VK_API_VERSION
        }
        res = requests.get(method_url, params=params).json()
        upload_url = res['response']['upload_url']

        # 2. Загружаем файл на сервер
        img_data = requests.get(image_url).content
        files = {'photo': ('image.jpg', img_data)}
        upload_res = requests.post(upload_url, files=files).json()

        # 3. Сохраняем фото в альбом группы
        method_url = "https://api.vk.com/method/photos.saveWallPhoto"
        params = {
            "group_id": VK_GROUP_ID.replace('-', ''),
            "photo": upload_res['photo'],
            "server": upload_res['server'],
            "hash": upload_res['hash'],
            "access_token": VK_USER_TOKEN,
            "v": VK_API_VERSION
        }
        save_res = requests.get(method_url, params=params).json()
        
        photo_data = save_res['response'][0]
        return f"photo{photo_data['owner_id']}_{photo_data['id']}"
    except Exception as e:
        print(f"Ошибка загрузки фото в VK: {e}")
        return None


def publish_to_vk(text, photo_url=None):
    """Публикует пост (текст + фото) на стену группы"""
    attachments = []
    
    if photo_url:
        photo_id = upload_photo_to_vk(photo_url)
        if photo_id:
            attachments.append(photo_id)

    method_url = "https://api.vk.com/method/wall.post"
    params = {
        "owner_id": f"-{VK_GROUP_ID.replace('-', '')}", # ID группы должен быть с минусом
        "from_group": 1,
        "message": text,
        "attachments": ",".join(attachments) if attachments else "",
        "access_token": VK_USER_TOKEN,
        "v": VK_API_VERSION
    }
    
    try:
        res = requests.post(method_url, data=params).json()
        if 'response' in res:
            return str(res['response']['post_id'])
        else:
            print(f"Ошибка VK API: {res.get('error')}")
    except Exception as e:
        print(f"Ошибка публикации в VK: {e}")
    return None


def delete_vk_post(post_id):
    """Удаляет пост из VK"""
    method_url = "https://api.vk.com/method/wall.delete"
    params = {
        "owner_id": f"-{VK_GROUP_ID.replace('-', '')}",
        "post_id": post_id,
        "access_token": VK_USER_TOKEN,
        "v": VK_API_VERSION
    }
    try:
        res = requests.get(method_url, params=params).json()
        return res.get('response') == 1
    except Exception as e:
        print(f"Ошибка удаления из VK: {e}")
        return False