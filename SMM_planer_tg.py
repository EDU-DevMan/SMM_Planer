import os
import requests
import time
from dotenv import load_dotenv
from datetime import datetime

from SMM_google_parser import get_client_authorization, SPREADSHEET_NAME, WORKSHEET_NAME
from SMM_timers import get_publication_time_match, get_match_time_post_deleted
from SMM_typography import processes_text_additionally


SOCIAL = "TG"
load_dotenv()


def send_to_telegram(text, photo_url=None):
    bot_token = os.environ.get('TG_BOT_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    
    if not bot_token or not chat_id:
        raise Exception("TG_BOT_TOKEN или TG_CHAT_ID не найдены в .env")
    
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
    bot_token = os.environ.get('TG_BOT_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    
    if not bot_token or not chat_id:
        raise Exception("TG_BOT_TOKEN или TG_CHAT_ID не найдены в .env")
    
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


def update_message_id(row_index, message_id):
    """Записывает message_id в колонку 'message_id'"""
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    headers = sheet.row_values(1)
    col_num = headers.index('message_id') + 1
    sheet.update_cell(row_index, col_num, message_id)


def get_message_id(row_index):
    """Читает message_id из колонки 'message_id'"""
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    headers = sheet.row_values(1)
    col_num = headers.index('message_id') + 1
    val = sheet.cell(row_index, col_num).value
    return int(val) if val and str(val).isdigit() else None


def clear_message_id(row_index):
    """Очищает ячейку message_id после удаления"""
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    headers = sheet.row_values(1)
    col_num = headers.index('message_id') + 1
    sheet.update_cell(row_index, col_num, "")


def run_once(records=None, timings=None, delete_timings=None):
    """Один цикл проверки для вызова из main.py с поддержкой кешированных данных"""
    try:
        # Если данные не переданы - читаем сами (для обратной совместимости)
        if records is None:
            client = get_client_authorization()
            sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
            records = sheet.get_all_records()
        
        if timings is None:
            timings = get_publication_time_match(records)
        
        if delete_timings is None:
            delete_timings = get_match_time_post_deleted(records)
        
        for i, row in enumerate(records, start=2):
            post_id = row.get('Ids')
            if not post_id:
                continue
            
            # ----- Публикация (только по флагу TG, без проверки статуса) -----
            tg_flag = str(row.get('TG', '')).strip()
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
                            print(f"  Пост {post_id} опубликован, message_id={message_id}")
                            update_tg_status(i, "Опубликовано")
                            update_message_id(i, message_id)
                        else:
                            print(f"  Ошибка публикации поста {post_id}")
                            update_tg_status(i, "Ошибка")
                    except Exception as e:
                        print(f"  Ошибка: {e}")
                        update_tg_status(i, "Ошибка")
            
            # ----- Удаление с правильной обработкой чекбокса -----
            delete_match = next((t for t in delete_timings if t['Ids'] == post_id), None)
            if delete_match and delete_match['timing_delete']:
                # Корректно обрабатываем значение чекбокса из таблицы
                auto_delete_raw = row.get('Удалить автоматически?', False)
                
                # Приводим к bool (работает и для TRUE/FALSE, и для True/False, и для строк)
                if isinstance(auto_delete_raw, str):
                    auto_delete = auto_delete_raw.strip().upper() == "TRUE"
                else:
                    auto_delete = bool(auto_delete_raw)
                
                if not auto_delete:
                    continue  # галочка не стоит — пропускаем удаление
                
                message_id = get_message_id(i)
                if message_id:
                    try:
                        if delete_message(message_id):
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Пост {post_id} удален")
                            clear_message_id(i)
                            update_tg_status(i, "Удалено")
                        else:
                            print(f"  Не удалось удалить пост {post_id}")
                    except Exception as e:
                        print(f"  Ошибка удаления поста {post_id}: {e}")
                else:
                    print(f"  message_id для поста {post_id} не найден в таблице")
                        
    except Exception as e:
        print(f"Ошибка в run_once: {e}")


def main():
    """Режим самостоятельного запуска (с бесконечным циклом)"""
    print(f"Telegram SMM Planer запущен {datetime.now().strftime('%H:%M:%S')}")
    while True:
        run_once()
        time.sleep(30)


if __name__ == '__main__':
    main()