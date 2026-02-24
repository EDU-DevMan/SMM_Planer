from googleapiclient.discovery import build
from google.oauth2 import service_account
import re


def get_text_from_google_doc(doc_url, credentials_file='creds.json'):
    try:
        doc_id = extract_doc_id(doc_url)
        if not doc_id:
            print(f"Ошибка извлечения ID из ссылки: {doc_url}")
            return None

        creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )

        service = build('docs', 'v1', credentials=creds)
        document = service.documents().get(documentId=doc_id).execute()
        text = extract_text_from_document(document)

        return text

    except Exception as e:
        print(f"Ошибка чтения Google Doc: {e}")
        return None


def extract_doc_id(url):
    match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None


def extract_text_from_document(document):
    text = []
    content = document.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' in element:
            paragraph = element.get('paragraph', {})
            paragraph_text = []

            for paragraph_element in paragraph.get('elements', []):
                if 'textRun' in paragraph_element:
                    paragraph_text.append(
                        paragraph_element['textRun'].get('content', ''))

            text.append(''.join(paragraph_text))

    return '\n'.join(text).strip()
