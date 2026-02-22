import logging
import schedule
import time
import os

from SMM_typography import processes_text_additionally
from SMM_google_parser import get_data_from_sheet
from SMM_planer_tg import run_once as run_tg_once
from SMM_planer_ok import run_once as run_ok_once  # Теперь работает


LOGS_PATH = "logs"


def generates_log():
    os.makedirs(LOGS_PATH, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/SMM_planer.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


def run_smm_typography():
    generates_log().info("Корректируем текст")
    try:
        data = get_data_from_sheet()
        if data:
            for row in data:
                text = row.get('Текст поста', '')
                if text:
                    cleaned = processes_text_additionally(text)
                    generates_log().info(f"Очищенный текст: {cleaned[:50]}...")
        generates_log().info("Корректировка успешна")
    except Exception as e:
        generates_log().error(f"Ошибка - {e}")


def run_tg_cycle():
    generates_log().info("Запуск проверки Telegram")
    try:
        run_tg_once()
        generates_log().info("Проверка Telegram завершена")
    except Exception as e:
        generates_log().error(f"Ошибка Telegram - {e}")


def run_ok_cycle():
    generates_log().info("Запуск проверки OK")
    try:
        run_ok_once()
        generates_log().info("Проверка OK завершена")
    except Exception as e:
        generates_log().error(f"Ошибка OK - {e}")


def run_get_data_from_sheet():
    generates_log().info("Читаем таблицу")
    try:
        data = get_data_from_sheet()
        generates_log().info(f"Найдено записей: {len(data)}")
        generates_log().info("Таблица прочитана успешно")
    except Exception as e:
        generates_log().error(f"Ошибка - {e}")


def runs_tasks_schedule():
    generates_log().info("SMM Planer запущен...")

    schedule.every(30).seconds.do(run_tg_cycle)
    schedule.every(30).seconds.do(run_ok_cycle)
    schedule.every(60).seconds.do(run_get_data_from_sheet)
    schedule.every(5).minutes.do(run_smm_typography)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        runs_tasks_schedule()
    except KeyboardInterrupt:
        generates_log().info("Выполнение остановлено")
    except Exception as e:
        generates_log().critical(f"Ошибка: {e}")