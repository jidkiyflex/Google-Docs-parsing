"""
    TEST
"""
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Константы для тестовых запусков

URL = 'https://confluence.hflabs.ru/pages/viewpage.action?pageId=1181220999'
# URL = 'https://confluence.hflabs.ru/pages/viewpage.action?pageId=207454320'
# URL = 'https://confluence.hflabs.ru/pages/viewpage.action?pageId=480542795'
# URL = 'https://yandex.ru'

DOCUMENT_ID = '1yXfjM6HLO3JMeVguEG4rF-UTEhwG0qWRctbjzYnAtn0'
SERVICE_ACCOUNT_FILE = 'parce-375516-61b08001826e.json'


def get_kb_html_table(url: str, timeout=5) -> str:
    """ Функция извлекает таблицу из confluence по адресу url и возвращает её
        в чистом, очищенном от стилей html.
        Для идентификации ячеек используются тэги классов стилей confluence
        из body страницы: confluenceTh и confluenceTd.
        timeout - время ожидания ответа от сервера по адресу url
    """
    # учитываем timeout, чтобы не зависло и не сломалось дальше
    try:
        response = requests.get(url, timeout = timeout)
    except requests.exceptions.Timeout:
        return 'ERROR'

    if response.status_code != 200:    # С сервером проблемы
        return 'ERROR'

    soup = BeautifulSoup(response.text, "html.parser")

    tbl_data = []        # Список, строк таблицы (row_data)
    tbl_data_row = []    # Список, данные в столбцах строки


    raw_header = soup.find_all('th', class_='confluenceTh')
    col_cnt = len(raw_header)

    if col_cnt == 0 or col_cnt > 50:
        # Что-то подозрительное со столбцами таблицы (нет/много)
        return 'ERROR'

    # Строка 0 - заголовки
    for col in raw_header:
        tbl_data_row.append(col.text)

    tbl_data.append(tbl_data_row)

    raw_data = soup.find_all('td', class_='confluenceTd')

    tbl_data_row = []
    for i, cell in enumerate(raw_data, 1):
        tbl_data_row.append(cell.text)
        if i%col_cnt == 0:
            tbl_data.append(tbl_data_row)
            tbl_data_row = []

    return tbl_data


def send_tbl_to_google_docs(tbl_data: list(), document_id: str,
                            service_account_file: str, is_del_cur=True) -> str:
    """ Функция получает данные таблицы в списке tbl_data
        и публикует их в google docs (document_id)
        service_account_file - имя файла с ключом для аутентификация в гугле
        is_del_cur - предварительно удалить текущую таблицу в гуглдоке?
    """

    # Подготовка и отправка документа

    row_cnt = len(tbl_data)
    if row_cnt <= 0:   # Выход, если получен пустой список (пустая таблица)
        return 'ERROR'

    col_cnt = len(tbl_data[0])
    req = []

    idx = 2
    for i, row in enumerate(tbl_data, 0):
        idx += 3
        for j, cell in enumerate(row, 0):
            if j != 0:
                idx += 2
            req.append({ "insertText": { "text": cell,
                                         "location": { "index": idx } } })

    req.append({ "insertTable": { "rows": row_cnt,
                                 "columns": col_cnt,
                                 "location": { "index": 1 } } })
    req.reverse()   # Особенность смещений индексов

    # Вход в Google Docs
    SCOPES = ['https://www.googleapis.com/auth/documents']
    credentials = service_account.Credentials.from_service_account_file(
                                  service_account_file, scopes=SCOPES)
    try:
        service = build('docs', 'v1', credentials=credentials)

        # Удаление таблицы в гуглдоке
        if is_del_cur:
            document = service.documents().get(documentId=DOCUMENT_ID).execute()
            table = document['body']['content'][2]
            requests = [{
                  'deleteContentRange': {
                    'range': {
                      'segmentId': '',
                      'startIndex': table['startIndex'],
                      'endIndex':   table['endIndex']
                    }
                  },
              }
              ]
            result = service.documents().batchUpdate(documentId=document_id,
                                        body={'requests': requests}).execute()

        result = service.documents().batchUpdate(documentId = document_id,
                                            body = {'requests': req}).execute()
        return 'OK'

    except HttpError :
        return 'ERROR'



if __name__ == '__main__':
    tbl_data = get_kb_html_table(URL)
    if tbl_data != 'ERROR':
        print(send_tbl_to_google_docs(tbl_data,
                                      DOCUMENT_ID,
                                      SERVICE_ACCOUNT_FILE))
