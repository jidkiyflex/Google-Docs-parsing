"""
Парсинг таблицы confluence HFL  n столбцов
"""
import requests
from bs4 import BeautifulSoup

URL = 'https://confluence.hflabs.ru/pages/viewpage.action?pageId=1181220999'
# URL = 'https://confluence.hflabs.ru/pages/viewpage.action?pageId=207454320'
# URL = 'https://confluence.hflabs.ru/pages/viewpage.action?pageId=480542795'
# URL = 'https://yandex.ru'

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

    raw_header = soup.find_all('th', class_='confluenceTh')
    col_cnt = len(raw_header)

    if col_cnt == 0 or col_cnt > 50:
        # Что-то подозрительное со столбцами таблицы (нет/много)
        return 'ERROR'

    header = '<thead><tr>'
    for header_item in raw_header:
        header = f'{header}<th>{header_item.text}</th>'

    header = f'{header}</tr></thead>'

    raw_data = soup.find_all('td', class_='confluenceTd')

    table_html = f'<table border="1">{header}<tbody>'
    nr = True        # Маркер начала новой строки
    for i, row in enumerate(raw_data, 1):
        cur_cell = str(row).replace(' class="confluenceTd"','')
        if i%col_cnt != 0:
            if nr:   # Первый столбец, начало строки
                table_html = f'{table_html}<tr>{cur_cell}'
                nr = False
            else:    # Не первый, не последний
                table_html = f'{table_html}{cur_cell}'
        else:        # Последний столбец, конец строки
            table_html = f'{table_html}{cur_cell}</tr>'
            nr = True

    table_html = f'{table_html}</tbody></table>'
    return table_html


print(get_kb_html_table(URL))