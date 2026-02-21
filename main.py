import logging
import schedule
import time
import os

from SMM_typography import main
from SMM_google_parser import get_data_from_sheet


LOGS_PATH = "logs"


def generates_log():
    "Функция гененерирует логи работы schedule"

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
    """Запускает модуль typography.py"""

    generates_log().info("Корректируем текст")
    try:
        # TODO: Взял для примера несколько модулей для запуска
        print(main())
        generates_log().info("Корректировка успешна")
    except Exception as e:
        generates_log().error(f"Ошибка - {e}")


def run_get_data_from_sheet():
    """Запускает модуль SMM_google_parser.py"""
    generates_log().info("Читаем таблицу")
    try:
        # TODO: Взял для примера несколько модулей для запуска
        print(get_data_from_sheet())
        generates_log().info("Таблица прочитана успешно")
    except Exception as e:
        generates_log().error(f"Ошибка - {e}")


def runs_tasks_schedule():
    """Настройка расписания"""

    # TODO: Пример взял вот тут:  https://pypi.org/project/schedule/
    generates_log().info("SMM Planer запущен...")

    schedule.every(10).seconds.do(run_smm_typography)
    schedule.every(20).seconds.do(run_get_data_from_sheet)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":

    try:
        runs_tasks_schedule()
    except KeyboardInterrupt:
        generates_log().info("Выполения остановлено")
    except Exception as e:
        generates_log().critical(f"Ошибка: {e}")
