import gspread
from google.oauth2 import service_account


GOOGLE_CREDENTIALS = 'creds.json'

SCOPE_CREDENTIALS = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]

SPREADSHEET_NAME = "SMM_Planer_Vitaliy"
WORKSHEET_NAME = "Plan"


def get_client_authorization():
    """Функция получает авторизованного пользователя"""

    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS,
            scopes=SCOPE_CREDENTIALS
        )
        return gspread.authorize(creds)

    except FileNotFoundError:
        print(f"Файл {GOOGLE_CREDENTIALS} не найден")
    except Exception as e:
        print(f"Ошибка авторизации: {type(e).__name__} - {e}")

    return None


def get_data_from_sheet():
    """Функция возвращает данные из таблицы"""

    try:
        spreadsheet = get_client_authorization().open(SPREADSHEET_NAME)
        sheet = get_client_authorization().open_by_key(
            spreadsheet.id).worksheet(WORKSHEET_NAME)
        data = sheet.get_all_records()

        return data

    except gspread.exceptions.SpreadsheetNotFound:
        return "Таблица с таким именем не найдена."
    except gspread.exceptions.WorksheetNotFound:
        return "Лист с таким именем не найден."
    except Exception:
        return "Невозможно вернуть данные."


if __name__ == "__main__":
    print(get_data_from_sheet())
