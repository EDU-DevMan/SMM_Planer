import os
import requests
from dotenv import load_dotenv

load_dotenv()


def send_to_telegram(text, photo_url=None):
    """Публикует пост и возвращает message_id (или None при ошибке)"""
    bot_token = os.environ.get('TG_BOT_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("TG_BOT_TOKEN или TG_CHAT_ID не найдены")
        return None
    
    try:
        if photo_url and photo_url.strip().startswith('http'):
            is_gif = photo_url.split('?')[0].lower().endswith('.gif')
            
            if is_gif:
                url = f"https://api.telegram.org/bot{bot_token}/sendAnimation"
                payload = {'chat_id': chat_id, 'animation': photo_url, 'caption': text[:1024] if text else ""}
            else:
                url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                payload = {'chat_id': chat_id, 'photo': photo_url, 'caption': text[:1024] if text else ""}
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {'chat_id': chat_id, 'text': text}
        
        response = requests.post(url, data=payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get('ok'):
            return result['result'].get('message_id')
        else:
            print(f"Ошибка API TG: {result}")
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")
    
    return None


def delete_message(message_id):
    """Удаляет сообщение по ID и возвращает True/False"""
    bot_token = os.environ.get('TG_BOT_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    
    url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"
    payload = {'chat_id': chat_id, 'message_id': message_id}
    
    try:
        response = requests.post(url, data=payload)
        return response.json().get('ok', False)
    except Exception as e:
        print(f"Ошибка удаления из TG: {e}")
        return False