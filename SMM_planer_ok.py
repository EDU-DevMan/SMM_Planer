import requests
import json
import time

from ok_api import OkApiException
from SMM_timers import get_publication_time_match, get_match_time_post_deleted
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
            return response.json()

        except OkApiException as e:
            print(f"Ошибка API OK ({e.error_code}): {e.message}. Ждем 30 сек")
            time.sleep(30)


def delete_from_ok(post_id):
    try:
        clean_id = str(post_id).replace('"', '').replace("'", "").strip()
        response = ok_access.mediatopic.deleteTopic(
            topic_id=clean_id
        )
        if hasattr(response, 'json'):
            result = response.json()
        else:
            result = response
        if isinstance(result, dict) and 'error_code' in result:
            print(f"Ошибка ОК: {result.get('error_msg')}")
            return False
        return True

    except OkApiException as e:
        print(f"Ошибка API ({e.error_code}): {e.message}")
        return False

def main():
    client = get_client_authorization()
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    header = sheet.find("Статус OK")
    status_col_num = header.col
    while True:
        records = sheet.get_all_records()
        time_matches = get_publication_time_match()
        publish_map = {item['Ids']: item['timing_post'] for item in time_matches}

        delete_matches = get_match_time_post_deleted()
        delete_map = {item['Ids']: item['timing_delete'] for item in delete_matches}

        for i, row in enumerate(records, start=2):
            ok_flag = str(row.get("OK"))
            status = str(row.get("Статус OK"))
            post_id = row.get("Ids")
            if ok_flag == "1" and (status == "Запланировано" or status == ""):
                text_post = row.get("Текст поста")
                photo_url = row.get("Ссылка на фото")
                if not publish_map.get(post_id):
                    continue
                photo_token = None
                if photo_url:
                    print("Загружаю фото...")
                    photo_token = upload_photo(photo_url)
                    if not photo_token:
                        sheet.update_cell(i, status_col_num, "Ошибка")
                        continue
                res = post_to_ok(text_post, photo_token)
                print("Успех")
                sheet.update_cell(i, status_col_num, f"Опубликовано:{res}")
                break

            elif ok_flag == "1" and status.startswith("Опубликовано"):
                if not delete_map.get(post_id):
                    continue
                raw_id = status.split(":")[1]
                ok_post_id = raw_id.replace('"', '').strip()
                delete_from_ok(ok_post_id)
                sheet.update_cell(i, status_col_num, "Удалено")
                break
        time.sleep(60)

if __name__ == "__main__":
    main()