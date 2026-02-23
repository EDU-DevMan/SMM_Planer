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
    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS, scopes=SCOPE_CREDENTIALS
        )
        return gspread.authorize(creds)
    except Exception as e:
        print(f"Ошибка авторизации Google: {e}")
        return None


def get_sheet_and_data():
    """Возвращает объект листа, заголовки и все записи"""
    try:
        client = get_client_authorization()
        if not client:
            return None, None, None
            
        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
        headers = sheet.row_values(1)
        records = sheet.get_all_records()
        return sheet, headers, records
    except Exception as e:
        print(f"Ошибка получения данных: {e}")
        return None, None, None


def batch_update_cells(sheet, cell_objects):
    """Массовое обновление ячеек одним запросом"""
    if sheet and cell_objects:
        try:
            sheet.update_cells(cell_objects)
        except Exception as e:
            print(f"Ошибка при обновлении ячеек: {e}")