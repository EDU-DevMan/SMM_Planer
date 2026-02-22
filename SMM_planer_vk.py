import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime, timedelta
from SMM_google_parser import get_data_from_sheet



def update_google_sheets_status(row_id, status_vk, vk_post_id=None):
    """Обновляет статус поста в Google Sheets""" 
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('creds.json', scopes=scope)
        gc_local = gspread.authorize(creds)
        
        sheet_key = '11F5HHCqIaRua-FyVDBZd98MJOS8L-S_wLny9aPBvhQw'
        sheet = gc_local.open_by_key(sheet_key).sheet1
        
        if vk_post_id:
            status_text = 'Опубликовано'
        else:
            status_text = status_vk
            
        sheet.update_cell(row_id + 1, 8, status_text)
        # print(f'Статус обновлён для строки {row_id}: {status_text}')    # отладочный принт
        
    except Exception as e:
        print(f'Ошибка Google Sheets: {e}')

def get_publication_time_match():
    """Функция находит посты для публикации в группе ВК"""
    results = []
    now = datetime.now()

    for index, row in enumerate(get_data_from_sheet()):
        date = row.get('Дата')
        time = row.get('Время')
        
        if not all([date, time]):
            continue
            
        clean_time = ":".join(time.strip().split(":")[:2])
        try:
            post_date = datetime.strptime(f"{date} {clean_time}", "%d.%m.%Y %H:%M")
            timing_post = abs((now - post_date).total_seconds()) <= 60
        except ValueError:
            continue

        results.append({
            'row_id': index + 1,
            'Ids': row.get('Ids'),
            'timing_post': timing_post,
            'VK': row.get('VK'),
            'text': row.get('Текст поста'),
            'photo_url': row.get('Ссылка на фото')
        })
    return results

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
    photo_id = f'photo{save_response['response'][0]['owner_id']}_{save_response['response'][0]['id']}'
    return photo_id

def post_to_vk(text, photo_id=None):
    """Публикация поста в группе ВК"""
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

    if photo_id:
        payload['attachments'] = photo_id

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
        print(f'HTTP ошибка: {e}')
        return None

def get_match_time_post_deleted():
    results = []
    now = datetime.now()
    
    for index, row in enumerate(get_data_from_sheet()):
        post_id = row.get('VK_post_ID')
        delete_auto = row.get('Удалить автоматически?')
        delete_datetime = row.get('Удалить')
        
        if (post_id and delete_auto == 'TRUE' and delete_datetime and delete_datetime != 'None'):
            try:
                delete_time = datetime.strptime(delete_datetime.strip(), "%d.%m.%Y %H:%M:%S")
                time_diff = abs((delete_time - now).total_seconds())
                is_delete_time = time_diff <= 60
                
                if is_delete_time:
                    results.append({
                        'row_id': index + 1,
                        'Ids': post_id,
                        'timing_delete': True,
                    })
                    print(f'Удаляю публикацию с ID:{post_id}')
                    
            except ValueError as e:
                print(f'Неверный формат даты: {e}')
    return results

def delete_vk_post(post_id, group_id):
    try:
        url = 'https://api.vk.com/method/wall.delete'
        payload = {
            'access_token': os.environ['VK_USER_TOKEN'],
            'owner_id': f'-{group_id}',
            'post_id': post_id,
            'v': '5.199'
        }
        # print(f'Удаляю: owner_id=-{group_id}, post_id={post_id}')    # отладочный принт
        
        response = requests.post(url, data=payload)
        result = response.json()
        # print(f'ОТВЕТ VK API: {result}')    # отладочный принт
        
        if 'response' in result:
            print(f'Публикация {post_id} удалена!')
            return True
        elif 'error' in result:
            print(f'Ошибка VK #{result['error']['error_code']}: {result['error']['error_msg']}')
            return False
        else:
            print(f'НЕИЗВЕСТНЫЙ ОТВЕТ: {result}')
            return False
            
    except Exception as e:
        print(f'Ошибка: {e}')
        return False

def main():
    """Основная функция для размещения поста в группе ВК"""
    load_dotenv()
    vk_group_key = os.environ['VK_GROUP_KEY']
    vk_group_id = os.environ['VK_GROUP_ID']
    user_token = os.environ['VK_USER_TOKEN']

    print(f'ТЕКУЩЕЕ ВРЕМЯ: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}')

    print('Проверяю наличие актуальных публикаций...')
    posts_to_publish = get_publication_time_match()
    
    for post in posts_to_publish:
        if post['timing_post'] and post['VK']:
            print(f'Публикую, строка (Ids) {post['row_id']}')    # отладочный принт
            
            update_google_sheets_status(post['row_id'], 'Запланировано')
            
            vk_post_id = None
            if post['photo_url']:
                photo_id = upload_wall_photo(user_token, vk_group_id, post['photo_url'])
                if photo_id:
                    vk_post_id = post_to_vk(post['text'], photo_id)
                else:
                    vk_post_id = post_to_vk(post['text'])
            else:
                vk_post_id = post_to_vk(post['text'])
            
            if vk_post_id:
                update_google_sheets_status(post['row_id'], 'Опубликовано', vk_post_id)
                # print(f'Опубликовано! VK ID: {vk_post_id}')    # отладочный принт
                try:
                    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                    creds = Credentials.from_service_account_file('creds.json', scopes=scope)
                    gc = gspread.authorize(creds)
                    sheet = gc.open_by_key('11F5HHCqIaRua-FyVDBZd98MJOS8L-S_wLny9aPBvhQw').sheet1
                    sheet.update_cell(post['row_id'] + 1, 14, vk_post_id)  # N=14
                    # print(f'VK_post_ID {vk_post_id} сохранён в N{post['row_id']+1}')    # отладочный принт
                except:
                    pass               
            else:
                update_google_sheets_status(post['row_id'], 'Ошибка')
    
    print('Проверяю наличие постов для удаления...')
    posts_to_delete = get_match_time_post_deleted()
    for post in posts_to_delete:
        if post['timing_delete'] and post['Ids']:
            # print(f'Удаляю пост {post['Ids']}')   # отладочный принт
            success = delete_vk_post(post['Ids'], vk_group_id)
            if success:
                update_google_sheets_status(post['row_id'], 'Удалено')
    
    print('Проверка завершена!')


if __name__ == '__main__':
    main()