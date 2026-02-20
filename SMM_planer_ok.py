import requests
import json
import time

from ok_api import OkApiException
from ok_config import ok_access, OK_GROUP_ID
from SMM_google_parser import get_client_authorization, SPREADSHEET_NAME, WORKSHEET_NAME


def upload_photo(image_url):
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
            return response

        except OkApiException as e:
            print(f"   Ошибка API OK ({e.error_code}): {e.message}. Ждем 30 сек")
            time.sleep(30)


def main():
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    records = sheet.get_all_records()
    print(f"Таблица подключена. Строк: {len(records)}")
    for i, row in enumerate(records, start=2):
        ok_flag = str(row.get('OK'))
        if ok_flag == "1":
            text_post = row.get("Текст поста")
            photo_url = row.get("Ссылка на фото")
            photo_token = None
            if photo_url:
                print("Загружаю фото...")
                photo_token = upload_photo(photo_url)
                if not photo_token:
                    print("Не удалось загрузить фото.")
                    sheet.update_cell(i, 9, "Ошибка фото")
            print("Публикую в ОК...")
            res = post_to_ok(text_post, photo_token)
            print(f"Успешно! Ответ: {res}")
            sheet.update_cell(i, 9, "Опубликовано")
            break

if __name__ == "__main__":
    main()