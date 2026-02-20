import re
from SMM_google_parser import get_data_from_sheet

"""
Все комментарии и предложения из этого скрипта должны быть
перенесены в README|CONTRIBUTING при создании основного релиза
"""


def get_raw_text(text_raw):
    """Функция возвращает сырой текст из поля 'Текст поста'"""

    return text_raw['Текст поста']


def processes_text_additionally(text):
    """Функция возвращает очищенный текст из поля 'Текст поста'"""

    rules = [
        (r'\s+', ' '),                  # 1. Убираем лишние пробелы
        (r'"([^"]*)"', r'«\1»'),        # 2. Двойные кавычки
        (r"'([^']*)'", r'«\1»'),        # 3. Одинарные кавычки
        (r'\s--\s', ' — '),             # 4. Два дефиса в тире
        (r'\s-\s', ' — '),              # 5. Один дефис в тире
        (r'\s+([.,!?;:])', r'\1'),      # 6. Пробелы перед знаками
    ]

    for pattern, replacement in rules:
        text = re.sub(pattern, replacement, text)

    return text.strip()


if __name__ == "__main__":
    # TODO: продумать каким образом нам будет удобно получать результат
    # В данном случае идет привязка к 'Ids' из таблицы

    for text_raw in get_data_from_sheet():
        print(processes_text_additionally(
            get_raw_text(text_raw)),
            text_raw.get('Ids'))
