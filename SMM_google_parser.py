import gspread
from oauth2client.service_account import ServiceAccountCredentials


GOOGLE_CREDENTIALS = 'creds.json'

SCOPE_CREDENTIALS = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]

SPREADSHEET_NAME = "SMM_Planer_Vitaliy"
WORKSHEET_NAME = "Plan"


def get_account():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_CREDENTIALS,
        SCOPE_CREDENTIALS
        )

    return gspread.authorize(creds)


def get_data_from_sheet():
    """Функция возвращает данные из таблицы"""
    try:
        spreadsheet = get_account().open(SPREADSHEET_NAME)
        sheet = get_account().open_by_key(
            spreadsheet.id).worksheet(WORKSHEET_NAME)
        data = sheet.get_all_records()
        # all_values = sheet.get_all_values()

        # TODO: подумать с выводом
        return data

    except gspread.exceptions.SpreadsheetNotFound:
        print("Таблица с таким именем не найдена.")
    except gspread.exceptions.WorksheetNotFound:
        print("Лист с таким именем не найден.")


if __name__ == "__main__":
    result = get_data_from_sheet()

    if result:
        print(result)
