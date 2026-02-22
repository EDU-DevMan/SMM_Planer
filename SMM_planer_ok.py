import requests
import json
import time
from datetime import datetime

from ok_api import OkApiException
from ok_config import ok_access, OK_GROUP_ID
from SMM_google_parser import get_client_authorization, SPREADSHEET_NAME, WORKSHEET_NAME
from SMM_timers import get_publication_time_match, get_match_time_post_deleted
from SMM_typography import processes_text_additionally


def upload_photo(image_url):
    """Загружает фото в Одноклассники по URL"""
    if not isinstance(image_url, str) or not image_url.startswith('http'):
        print(f"  Некорректный URL фото: {image_url}")
        return None
    
    try:
        url_res = ok_access.photosV2.getUploadUrl(count=1, gid=str(OK_GROUP_ID)).json()
        upload_url = url_res["upload_url"]
        photo_id = url_res["photo_ids"][0]
        img_data = requests.get(image_url).content
        files = {"photo": (f"{photo_id}.jpg", img_data)}
        response = requests.post(upload_url, files=files)
        upload_res = response.json()

        if "photos" not in upload_res:
            print(f"ОК не принял файл. Ответ сервера: {upload_res}")
            return None
        photo_id = list(upload_res["photos"].keys())[0]
        return upload_res["photos"][photo_id]["token"]
    except Exception as e:
        print(f"Ошибка при загрузке фото: {e}")
        return None


def post_to_ok(text, photo_token=None):
    """Публикует пост в Одноклассники"""
    media = []
    if text:
        media.append({"type": "text", "text": text})
    if photo_token:
        media.append({"type": "photo", "list": [{"id": photo_token}]})

    attachment = json.dumps({"media": media})
    while True:
        try:
            response = ok_access.mediatopic.post(
                gid=OK_GROUP_ID,
                type="GROUP_THEME",
                attachment=attachment
            )
            
            # Универсальная обработка ответа
            if isinstance(response, dict):
                return response
            elif hasattr(response, 'json'):
                return response.json()
            else:
                return json.loads(response)
                
        except OkApiException as e:
            print(f"   Ошибка API OK ({e.error_code}): {e.message}. Ждем 30 сек")
            time.sleep(30)
        except Exception as e:
            print(f"   Неизвестная ошибка: {e}")
            time.sleep(30)
            return None


def update_ok_status(row_index, status):
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    headers = sheet.row_values(1)
    col_num = headers.index('Статус OK') + 1
    sheet.update_cell(row_index, col_num, status)


def update_ok_post_id(row_index, ok_post_id):
    """Записывает post_id в колонку 'ok_post_id'"""
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    headers = sheet.row_values(1)
    col_num = headers.index('ok_post_id') + 1
    sheet.update_cell(row_index, col_num, ok_post_id)


def get_ok_post_id(row_index):
    """Читает post_id из колонки 'ok_post_id'"""
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    headers = sheet.row_values(1)
    col_num = headers.index('ok_post_id') + 1
    val = sheet.cell(row_index, col_num).value
    return int(val) if val and str(val).isdigit() else None


def clear_ok_post_id(row_index):
    """Очищает ячейку ok_post_id после удаления"""
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    headers = sheet.row_values(1)
    col_num = headers.index('ok_post_id') + 1
    sheet.update_cell(row_index, col_num, "")


def delete_ok_post(post_id):
    """Удаляет пост в Одноклассниках по его ID"""
    try:
        # Метод удаления нужно уточнить в документации ok_api
        response = ok_access.mediatopic.delete(topic_id=post_id)
        return True
    except Exception as e:
        print(f"Ошибка удаления поста OK: {e}")
        return False


def run_once(records=None, timings=None, delete_timings=None):
    """Один цикл проверки для вызова из main.py с поддержкой кешированных данных"""
    try:
        # Если данные не переданы - читаем сами
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
            
            # ----- Публикация -----
            ok_flag = str(row.get('OK', '')).strip()
            if ok_flag == "1":
                timing = next((t for t in timings if t['Ids'] == post_id), None)
                if timing and timing['timing_post']:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Публикуем пост {post_id} в OK")
                    
                    raw_text = row.get('Текст поста', '')
                    cleaned_text = processes_text_additionally(raw_text)
                    
                    # Обработка фото
                    photo_url_raw = row.get('Ссылка на фото', '')
                    photo_url = str(photo_url_raw).strip() if photo_url_raw else ''
                    
                    try:
                        photo_token = None
                        if photo_url and photo_url.lower() not in ['none', 'null', ''] and photo_url.startswith('http'):
                            print("  Загружаю фото...")
                            photo_token = upload_photo(photo_url)
                            if not photo_token:
                                print("  Не удалось загрузить фото.")
                                update_ok_status(i, "Ошибка фото")
                                continue
                        
                        print("  Отправляем пост в OK...")
                        response_data = post_to_ok(cleaned_text, photo_token)
                        
                        print(f"  Ответ от OK: {response_data}")
                        
                        # ОК возвращает просто число - это и есть ID поста
                        ok_post_id = None
                        if isinstance(response_data, (str, int)):
                            ok_post_id = str(response_data)
                            print(f"  Получен ID поста: {ok_post_id}")
                        elif isinstance(response_data, dict):
                            ok_post_id = response_data.get('topic_id') or response_data.get('id') or response_data.get('post_id')
                            print(f"  Извлечённый ID: {ok_post_id}")
                        else:
                            print(f"  Неизвестный формат ответа: {type(response_data)}")
                        
                        if ok_post_id:
                            print(f"  Пост {post_id} опубликован, ok_post_id={ok_post_id}")
                            update_ok_status(i, "Опубликовано")
                            update_ok_post_id(i, ok_post_id)
                        else:
                            print(f"  НЕ УДАЛОСЬ получить ID поста из ответа!")
                            update_ok_status(i, "Ошибка")
                    except Exception as e:
                        print(f"  Ошибка: {e}")
                        update_ok_status(i, "Ошибка")
            
            # ----- Удаление -----
            delete_match = next((t for t in delete_timings if t['Ids'] == post_id), None)
            if delete_match and delete_match['timing_delete']:
                # Обработка чекбокса
                auto_delete_raw = row.get('Удалить автоматически?', False)
                
                if isinstance(auto_delete_raw, str):
                    auto_delete = auto_delete_raw.strip().upper() == "TRUE"
                else:
                    auto_delete = bool(auto_delete_raw)
                
                if not auto_delete:
                    continue
                
                saved_id = get_ok_post_id(i)
                if saved_id:
                    try:
                        if delete_ok_post(saved_id):
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Пост {post_id} удален из OK")
                            clear_ok_post_id(i)
                            update_ok_status(i, "Удалено")
                        else:
                            print(f"  Не удалось удалить пост {post_id} из OK")
                    except Exception as e:
                        print(f"  Ошибка удаления поста {post_id}: {e}")
                else:
                    print(f"  post_id для поста {post_id} не найден в таблице")
                        
    except Exception as e:
        print(f"Ошибка в run_once (OK): {e}")


def main():
    """Для самостоятельного запуска"""
    print(f"OK SMM Planer запущен {datetime.now().strftime('%H:%M:%S')}")
    while True:
        run_once()
        time.sleep(30)


if __name__ == '__main__':
    main()