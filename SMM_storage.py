import os

MESSAGES_FILE = "published_messages.txt"

def save_message_id(social, post_id, message_id):
    """Сохраняет message_id для поста в указанной соцсети"""
    with open(MESSAGES_FILE, "a", encoding="utf-8") as f:
        f.write(f"{social}|{post_id}|{message_id}\n")

def get_message_id(social, post_id):
    """Возвращает message_id для поста в соцсети или None"""
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 3 and parts[0] == social and parts[1] == str(post_id):
                    return int(parts[2])
    except FileNotFoundError:
        pass
    return None

def remove_message_id(social, post_id):
    """Удаляет запись о message_id для поста"""
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
            for line in lines:
                if not line.startswith(f"{social}|{post_id}|"):
                    f.write(line)
    except FileNotFoundError:
        pass