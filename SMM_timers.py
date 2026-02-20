from SMM_google_parser import get_data_from_sheet
from datetime import datetime


def get_publication_time_match():
    """
        Функция возвращает словарь:
        Пример:
        {'Ids': 1, 'timing_post': True},
        {'Ids': 2, 'timing_post': False}
        где Ids - ID поста, timing_post - время
        публикации совпадает с текущем временем (True или False)
    """
    # TODO: Важно учесть, что в переменную clean_seconds_time передаются
    #  минуты. В проде можем проверять до долей секунд...

    results = []

    for fields_date in get_data_from_sheet():
        date = fields_date.get('Дата')
        time = fields_date.get('Время')
        post_id = fields_date.get('Ids')

        clean_seconds_time = ":".join(time.strip().split(":")[:2])

        post_date = datetime.strptime(f"{date} {clean_seconds_time}",
                                      "%d.%m.%Y %H:%M")

        now_data = datetime.now().replace(second=0, microsecond=0)
        timing_post = post_date == now_data

        results.append({
            'Ids': post_id,
            'timing_post': timing_post,
        })

    return results


def get_match_time_post_deleted():
    """
        Функция возвращает словарь:
        Пример:
        {'Ids': 1, 'timing_delete': True},
        {'Ids': 2, 'timing_delete': False}
        где Ids - ID поста, timing_delete - время
        удаление публикации совпадает с текущем временем (True или False)
    """
    # TODO:

    results = []

    for fields_date in get_data_from_sheet():
        date = fields_date.get('Удалить через')
        post_id = fields_date.get('Ids')

        timing_delete = date == datetime.now().strftime("%d.%m.%Y")

        results.append({
            'Ids': post_id,
            'timing_delete': timing_delete,
        })

    return results


if __name__ == "__main__":

    print(get_publication_time_match())

    print(get_match_time_post_deleted())
