import os
import requests
from dotenv import load_dotenv

load_dotenv()

VK_USER_TOKEN = os.environ.get('VK_USER_TOKEN')
VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
VK_API_VERSION = '5.131'


def upload_photo_to_vk(img_data):
    """Загружает статичное фото на сервера VK и возвращает attachment ID"""
    if not img_data:
        return None

    try:
        method_url = "https://api.vk.com/method/photos.getWallUploadServer"
        params = {
            "group_id": VK_GROUP_ID.replace('-', ''),
            "access_token": VK_USER_TOKEN,
            "v": VK_API_VERSION
        }
        res = requests.get(method_url, params=params).json()
        upload_url = res['response']['upload_url']

        files = {'photo': ('image.jpg', img_data)}
        upload_res = requests.post(upload_url, files=files).json()

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


def upload_gif_to_vk(gif_data):
    """Загружает GIF как документ на сервера VK и возвращает attachment ID"""
    if not gif_data:
        return None

    try:
        method_url = "https://api.vk.com/method/docs.getWallUploadServer"
        params = {
            "group_id": VK_GROUP_ID.replace('-', ''),
            "access_token": VK_USER_TOKEN,
            "v": VK_API_VERSION
        }
        res = requests.get(method_url, params=params).json()
        upload_url = res['response']['upload_url']

        files = {'file': ('animation.gif', gif_data)}
        upload_res = requests.post(upload_url, files=files).json()

        method_url = "https://api.vk.com/method/docs.save"
        params = {
            "file": upload_res['file'],
            "access_token": VK_USER_TOKEN,
            "v": VK_API_VERSION
        }
        save_res = requests.get(method_url, params=params).json()
        
        doc_data = save_res['response']['doc']
        return f"doc{doc_data['owner_id']}_{doc_data['id']}"
    except Exception as e:
        print(f"Ошибка загрузки GIF в VK: {e}")
        return None


def publish_to_vk(text, media_url=None):
    """Публикует пост (текст + фото/GIF) на стену группы"""
    attachments = []
    
    if media_url and media_url.strip().startswith('http'):
        try:
            response = requests.get(media_url.strip())
            file_content = response.content
            
            content_type = response.headers.get('Content-Type', '').lower()
            is_gif = 'gif' in content_type or file_content.startswith(b'GIF8')
            
            if is_gif:
                media_id = upload_gif_to_vk(file_content)
            else:
                media_id = upload_photo_to_vk(file_content)
                
            if media_id:
                attachments.append(media_id)
        except Exception as e:
            print(f"Ошибка при скачивании/загрузке медиа для VK: {e}")

    method_url = "https://api.vk.com/method/wall.post"
    params = {
        "owner_id": f"-{VK_GROUP_ID.replace('-', '')}",
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