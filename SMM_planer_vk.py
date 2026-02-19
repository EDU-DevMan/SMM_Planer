import os
import requests
# import gspread
from dotenv import load_dotenv
from SMM_google_parser import get_data_from_sheet


def main():
    load_dotenv()
    vk_group_key = os.environ['VK_GROUP_KEY']
    vk_group_id = os.environ['VK_GROUP_ID']
    vk_url = 'https://api.vk.com/method/wall.post'
    payload = {
        'url': vk_url,
        'access_token': vk_group_key,
        'owner_id': f'-{vk_group_id}',
        'from_group': '1',
        'message': 'Ножи НКВД в наличии!!!',
        'v': '5.199'
    }
    response = requests.post(vk_url, data=payload)
    response.raise_for_status()
    post = response.json()
    if 'response' in post:
        print('Пост опубликован')
        # post['response']['post_id'] - id поста
    else:    
        print(f'Ошибка: {post['error']['error_text']}')

    result = get_data_from_sheet()
    # print(result)


if __name__ == '__main__':
    main()