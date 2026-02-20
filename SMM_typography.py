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


def main():
    """
        Функция возвращает словарь:
        Пример:
        {'Ids': 1, 'Corrected_text': 'C 23 февраля. «УРА!» — «УРА!» — «УРА!»'},
        {'Ids': 2, 'Corrected_text': 'C 8 марта. «УРА» — «УРА» — «УРА»!!!!'}
        где Ids - ID поста, Corrected_text - вычищенный текст
    """
    # TODO: продумать каким образом нам будет удобно получать результат
    # В данном случае идет привязка к 'Ids' из таблицы

    results = []

    for text_raw in get_data_from_sheet():
        results.append({
            'Ids': text_raw.get('Ids'),
            'Corrected_text': processes_text_additionally(
                get_raw_text(text_raw))
        })

    return results


if __name__ == "__main__":

    print(main())
