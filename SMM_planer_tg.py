import os
import requests
import time
from dotenv import load_dotenv
from datetime import datetime

from SMM_google_parser import get_client_authorization, SPREADSHEET_NAME, WORKSHEET_NAME
from SMM_timers import get_publication_time_match, get_match_time_post_deleted
from SMM_typography import processes_text_additionally
from SMM_storage import save_message_id, get_message_id, remove_message_id


SOCIAL = "TG"


def send_to_telegram(text, photo_url=None):
    bot_token = os.environ['TG_BOT_TOKEN']
    chat_id = os.environ['TG_CHAT_ID']
    
    if photo_url and photo_url.strip():
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        payload = {
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': text[:1024]
        }
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text
        }
    
    response = requests.post(url, data=payload)
    response.raise_for_status()
    result = response.json()
    
    if result['ok']:
        return result['result'].get('message_id')
    return None


def delete_message(message_id):
    bot_token = os.environ['TG_BOT_TOKEN']
    chat_id = os.environ['TG_CHAT_ID']
    url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"
    
    payload = {
        'chat_id': chat_id,
        'message_id': message_id
    }
    
    response = requests.post(url, data=payload)
    response.raise_for_status()
    result = response.json()
    return result.get('ok', False)


def update_tg_status(row_index, status):
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    headers = sheet.row_values(1)
    col_num = headers.index('Статус TG') + 1
    sheet.update_cell(row_index, col_num, status)


def main():
    load_dotenv()
    print(f"Telegram SMM Planer запущен {datetime.now().strftime('%H:%M:%S')}")
    
    while True:
        try:
            client = get_client_authorization()
            sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
            records = sheet.get_all_records()
            timings = get_publication_time_match()
            delete_timings = get_match_time_post_deleted()
            
            for i, row in enumerate(records, start=2):
                post_id = row.get('Ids')
                if not post_id:
                    continue
                
                # Публикация
                tg_flag = str(row.get('TG', ''))
                if tg_flag == "1":
                    timing = next((t for t in timings if t['Ids'] == post_id), None)
                    if timing and timing['timing_post']:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Публикуем пост {post_id}")
                        
                        raw_text = row.get('Текст поста', '')
                        cleaned_text = processes_text_additionally(raw_text)
                        photo_url = row.get('Ссылка на фото', '')
                        
                        try:
                            message_id = send_to_telegram(cleaned_text, photo_url)
                            if message_id:
                                print(f"  Пост {post_id} опубликован")
                                save_message_id(SOCIAL, post_id, message_id)
                                update_tg_status(i, "Опубликовано")
                            else:
                                print(f"  Ошибка публикации поста {post_id}")
                                update_tg_status(i, "Ошибка")
                        except Exception as e:
                            print(f"  Ошибка: {e}")
                            update_tg_status(i, "Ошибка")
                
                # Удаление
                delete_match = next((t for t in delete_timings if t['Ids'] == post_id), None)
                if delete_match and delete_match['timing_delete']:
                    message_id = get_message_id(SOCIAL, post_id)
                    if message_id:
                        try:
                            if delete_message(message_id):
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] Пост {post_id} удален")
                                remove_message_id(SOCIAL, post_id)
                                update_tg_status(i, "Удалено")
                        except Exception as e:
                            print(f"  Ошибка удаления поста {post_id}: {e}")
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\nСкрипт остановлен")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(30)


if __name__ == '__main__':
    main()