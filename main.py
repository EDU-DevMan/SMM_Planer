import logging
import time
import os
from datetime import datetime
from gspread import Cell

from SMM_typography import processes_text_additionally
from SMM_google_parser import get_sheet_and_data, batch_update_cells
import SMM_planer_tg as tg
import SMM_planer_ok as ok
import SMM_planer_vk as vk

LOGS_PATH = "logs"


def setup_logger():
    os.makedirs(LOGS_PATH, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{LOGS_PATH}/SMM_planer.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logger()


def parse_datetime(date_str, time_str=None):
    if not date_str: return None
    try:
        date_s = str(date_str).strip()
        if time_str:
            t_parts = str(time_str).strip().split(":")
            clean_time = f"{t_parts[0].zfill(2)}:{t_parts[1].zfill(2)}"
            return datetime.strptime(f"{date_s} {clean_time}", "%d.%m.%Y %H:%M")
        return datetime.strptime(date_s, "%d.%m.%Y %H:%M:%S")
    except: return None


def run_planner_cycle():
    logger.info("--- Начинаем цикл проверки ---")
    sheet, headers, records = get_sheet_and_data()
    if not records: return

    now = datetime.now()
    cells_to_update = []

    def get_idx(name): return headers.index(name) + 1 if name in headers else None

    # Индексы колонок для записи
    idx_tg_s, idx_tg_id = get_idx('Статус TG'), get_idx('message_id')
    idx_ok_s, idx_ok_id = get_idx('Статус OK'), get_idx('ok_post_id')
    idx_vk_s, idx_vk_id = get_idx('Статус VK'), get_idx('vk_post_id')

    for i, row in enumerate(records, start=2):
        post_id = row.get('Ids', f"Row {i}")
        text = processes_text_additionally(row.get('Текст поста', ''))
        img = str(row.get('Ссылка на фото', '')).strip()
        pub_time = parse_datetime(row.get('Дата'), row.get('Время'))
        
        # --- ПУБЛИКАЦИЯ ---
        if pub_time and now >= pub_time:
            # TG
            if str(row.get('TG')) == "1" and row.get('Статус TG') not in ["Опубликовано", "Удалено"]:
                logger.info(f"[{post_id}] Публикуем в Telegram...")
                res = tg.send_to_telegram(text, img)
                if res:
                    cells_to_update.extend([Cell(i, idx_tg_s, "Опубликовано"), Cell(i, idx_tg_id, str(res))])
                    row['Статус TG'] = "Опубликовано"
                    row['message_id'] = str(res)

            # OK
            if str(row.get('OK')) == "1" and row.get('Статус OK') not in ["Опубликовано", "Удалено"]:
                logger.info(f"[{post_id}] Публикуем в Одноклассники...")
                res = ok.publish_to_ok(text, img)
                if res:
                    cells_to_update.extend([Cell(i, idx_ok_s, "Опубликовано"), Cell(i, idx_ok_id, str(res))])
                    row['Статус OK'] = "Опубликовано"
                    row['ok_post_id'] = str(res)

            # VK
            if str(row.get('VK')) == "1" and row.get('Статус VK') not in ["Опубликовано", "Удалено"]:
                logger.info(f"[{post_id}] Публикуем в VK...")
                res = vk.publish_to_vk(text, img)
                if res:
                    cells_to_update.extend([Cell(i, idx_vk_s, "Опубликовано"), Cell(i, idx_vk_id, str(res))])
                    row['Статус VK'] = "Опубликовано"
                    row['vk_post_id'] = str(res)

        # --- УДАЛЕНИЕ ---
        is_del = str(row.get('Удалить автоматически?')).strip().upper() in ["TRUE", "1"]
        del_time = parse_datetime(row.get('Удалить'))

        if is_del and del_time and now >= del_time:
            # TG
            if row.get('Статус TG') == "Опубликовано" and row.get('message_id'):
                logger.info(f"[{post_id}] Удаляем из Telegram...")
                if tg.delete_message(row.get('message_id')):
                    cells_to_update.extend([Cell(i, idx_tg_s, "Удалено"), Cell(i, idx_tg_id, "")])
            
            # OK
            if row.get('Статус OK') == "Опубликовано" and row.get('ok_post_id'):
                logger.info(f"[{post_id}] Удаляем из Одноклассников...")
                if ok.delete_ok_post(row.get('ok_post_id')):
                    cells_to_update.extend([Cell(i, idx_ok_s, "Удалено"), Cell(i, idx_ok_id, "")])

            # VK
            if row.get('Статус VK') == "Опубликовано" and row.get('vk_post_id'):
                logger.info(f"[{post_id}] Удаляем из VK...")
                if vk.delete_vk_post(row.get('vk_post_id')):
                    cells_to_update.extend([Cell(i, idx_vk_s, "Удалено"), Cell(i, idx_vk_id, "")])

    if cells_to_update:
        batch_update_cells(sheet, cells_to_update)
        logger.info(f"Обновлено {len(cells_to_update)} ячеек в таблице.")
    
    logger.info("--- Цикл завершен ---")


def main():
    logger.info("SMM Planer запущен. Нажмите Ctrl+C для выхода.")
    while True:
        try:
            run_planner_cycle()
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        time.sleep(30) # Проверка каждые 30 секунд


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Работа планировщика остановлена пользователем.")
        # Вместо кучи строк Traceback выведется только эта короткая фраза