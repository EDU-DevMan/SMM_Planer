import logging
import schedule
import time
import os

from SMM_typography import main
from SMM_google_parser import get_data_from_sheet


"""
    > Все комментарии и предложения из этого скрипта должны быть
     перенесены в README|CONTRIBUTING при создании основного релиза
"""

"""
    Описание модуля schedule > https://pypi.org/project/schedule/
    Модуль позволяет запускать задания по расписанию.
    Для тестирования запуска по расписанию выполняются два задания:
    def run_smm_typography() и def run_get_data_from_sheet()
    Реализована запись логов работы generates_log() 
    в директорию logs - создается автоматически.
    """

# TODO: в основной реализации вместо тестовых заданий должны быть добавлены
# модули SMM_planer_ok.py | SMM_planer_tg.py | SMM_planer_vk.py

LOGS_PATH = "logs"


def generates_log():
    "Функция генерирует логи работы функция автозапуска"

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


# TODO: Пример автозапуска SMM_typography.py модуля
def run_smm_typography():
    """Запускает модуль typography.py"""

    generates_log().info("Корректируем текст")
    try:
        print(main())
        generates_log().info("Корректировка успешна")
    except Exception as e:
        generates_log().error(f"Ошибка - {e}")


# TODO: Пример автозапуска SMM_google_parser.py модуля
def run_get_data_from_sheet():
    """Запускает модуль SMM_google_parser.py"""
    generates_log().info("Читаем таблицу")
    try:
        print(get_data_from_sheet())
        generates_log().info("Таблица прочитана успешно")
    except Exception as e:
        generates_log().error(f"Ошибка - {e}")


def runs_tasks_schedule():
    """Запуск по расписанию"""

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
        generates_log().info("Выполнение остановлено")
    except Exception as e:
        generates_log().critical(f"Ошибка: {e}")
