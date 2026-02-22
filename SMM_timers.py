from SMM_google_parser import get_data_from_sheet
from datetime import datetime


def get_publication_time_match(records=None):
    """
    Возвращает список словарей с флагом публикации.
    Если records передан - использует его, иначе читает таблицу.
    """
    results = []
    
    # Если records не передан - читаем таблицу
    if records is None:
        records = get_data_from_sheet()

    for fields_date in records:
        date = fields_date.get('Дата')
        time = fields_date.get('Время')
        post_id = fields_date.get('Ids')
        
        if not date or not time:
            results.append({'Ids': post_id, 'timing_post': False})
            continue

        clean_seconds_time = ":".join(time.strip().split(":")[:2])
        post_date = datetime.strptime(f"{date} {clean_seconds_time}", "%d.%m.%Y %H:%M")
        now_data = datetime.now().replace(second=0, microsecond=0)
        results.append({'Ids': post_id, 'timing_post': post_date == now_data})

    return results


def get_match_time_post_deleted(records=None):
    """
    Возвращает список словарей с флагом удаления.
    Если records передан - использует его, иначе читает таблицу.
    """
    results = []
    now = datetime.now()
    
    # Если records не передан - читаем таблицу
    if records is None:
        records = get_data_from_sheet()

    for fields_date in records:
        delete_str = fields_date.get('Удалить через')
        post_id = fields_date.get('Ids')

        if not delete_str or not delete_str.strip():
            results.append({'Ids': post_id, 'timing_delete': False})
            continue

        try:
            delete_datetime = datetime.strptime(delete_str.strip(), "%d.%m.%Y %H:%M:%S")
            results.append({'Ids': post_id, 'timing_delete': now >= delete_datetime})
        except Exception:
            results.append({'Ids': post_id, 'timing_delete': False})

    return results


if __name__ == "__main__":
    print(get_publication_time_match())
    print(get_match_time_post_deleted())