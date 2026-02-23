import re


def processes_text_additionally(text):
    """Очищает текст от лишних символов и правит кавычки/тире"""
    if not text:
        return ""
        
    rules = [
        (r'\s+', ' '),                  # Убираем лишние пробелы
        (r'"([^"]*)"', r'«\1»'),        # Двойные кавычки
        (r"'([^']*)'", r'«\1»'),        # Одинарные кавычки
        (r'\s--\s', ' — '),             # Два дефиса в тире
        (r'\s-\s', ' — '),              # Один дефис в тире
        (r'\s+([.,!?;:])', r'\1'),      # Пробелы перед знаками
    ]

    for pattern, replacement in rules:
        text = re.sub(pattern, replacement, text)

    return text.strip()