from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException, ParserHTTPException


def get_response(session, url):
    """Выполняет запрос с обработкой ошибок."""
    try:
        response = session.get(url)
        response.encoding = "utf-8"
        return response
    except RequestException as e:
        raise ParserHTTPException(
            f"Ошибка при загрузке страницы {url}: {str(e)}"
        )


def find_tag(soup, tag, attrs=None, string=None):
    """Находит тег с обработкой ошибок."""
    searched_tag = soup.find(tag, attrs=(attrs or {}), string=string)
    if searched_tag is None:
        raise ParserFindTagException(f"Не найден тег {tag} {attrs}")
    return searched_tag


def fetch_and_parse(session, url):
    """Выполняет запрос и возвращает BeautifulSoup объект."""
    response = get_response(session, url)
    return BeautifulSoup(response.text, "lxml")
