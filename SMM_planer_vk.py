import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from SMM_google_parser import get_data_from_sheet


def upload_wall_photo(user_token, vk_group_id, photo_url):
    """Загрузка фото для поста в группе ВК"""
    upload_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    payload = {
        'access_token': user_token,
        'group_id': vk_group_id,
        'v': '5.199'
    }
    response = requests.get(upload_url, params=payload)
    upload_server = response.json()['response']  
    photo_for_post = requests.get(photo_url).content
    
    upload_response = requests.post(upload_server['upload_url'], files={'file': ('photo.jpg', photo_for_post, 'image/jpg')}).json()
    save_payload = {
        'group_id': vk_group_id,
        'photo': upload_response['photo'],
        'server': upload_response['server'],
        'hash': upload_response['hash'],
        'access_token': user_token,
        'v': '5.199'
    }
    save_response = requests.post(
        'https://api.vk.com/method/photos.saveWallPhoto', 
        data=save_payload
    ).json()
    photo_id = f"photo{save_response['response'][0]['owner_id']}_{save_response['response'][0]['id']}"
    return photo_id

def post_to_vk(text, photo_url=None):
    """ Публикация поста в группе ВК"""
    vk_group_key = os.environ['VK_GROUP_KEY']
    vk_group_id = os.environ['VK_GROUP_ID']
    vk_url = 'https://api.vk.com/method/wall.post'
    payload = {
        'access_token': vk_group_key,
        'owner_id': f'-{vk_group_id}',
        'from_group': '1',
        'message': text,
        'v': '5.199'
    }

    if photo_url:
        payload['attachments'] = photo_url

    try:
        response = requests.post(vk_url, data=payload)
        response.raise_for_status()
        post = response.json()
        if 'response' in post:
            print('Пост опубликован')
            return post['response']['post_id']
        else:    
            print(f'Ошибка: {post.get('error')}')
            return None
    except requests.exceptions.RequestException as e:
        print(f"HTTP ошибка: {e}")
        return None

def main():
    """Основная функция для размещения поста в группе ВК"""
    load_dotenv()
    vk_group_key = os.environ['VK_GROUP_KEY']
    vk_group_id = os.environ['VK_GROUP_ID']
    user_token = os.environ['VK_USER_TOKEN']

    print("Читаем Google Sheets...")
    data = get_data_from_sheet()
    
    for row in data:
        if row.get('VK'):
            text = row.get('Текст поста')
            photo_url = row.get('Ссылка на фото')
            photo_id = upload_wall_photo(user_token, vk_group_id, photo_url)
            post_to_vk(text, photo_id)


if __name__ == '__main__':
    main()