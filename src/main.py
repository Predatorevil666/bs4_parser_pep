import logging
import re

from urllib.parse import urljoin

import requests_cache

from bs4 import BeautifulSoup
from requests import RequestException
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    DOWNLOADS_DIR,
    EXPECTED_STATUS,
    LOG_ARCHIVE_SAVED,
    LOG_ARGS_CMD,
    LOG_CRITICAL_ERROR,
    LOG_CRITICAL_ERROR_IN_MODE,
    LOG_DOWNLOAD_ERROR,
    LOG_DOWNLOAD_START,
    LOG_PARSER_START,
    LOG_PARSER_STOP,
    LOG_PARSER_STOP_BY_USER,
    LOG_PARSER_VERSION_ERROR,
    LOG_RECIEVE_STATUS,
    LOG_SKIPP_PEP,
    LOG_SKIPP_VERSION,
    LOG_STATUS_MISMATCH_ENTRY,
    LOG_STATUS_MISMATCH_HEADER,
    LOG_UNEXPECTED_ERROR,
    MAIN_DOC_URL,
    PEP_URL,
)
from exceptions import ParserFindTagException, ParserHTTPException
from outputs import control_output
from utils import find_tag, get_response


def fetch_and_parse(session, url):
    """Выполняет запрос и возвращает BeautifulSoup объект."""
    try:
        response = get_response(session, url)
        return BeautifulSoup(response.text, "lxml")
    except ParserHTTPException as e:
        logging.error(str(e))
        return None


def whats_new(session):
    """Парсит список нововведений в Python из официальной документации."""
    errors = []
    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")
    soup = fetch_and_parse(session, whats_new_url)
    if not soup:
        return None

    results = [("Ссылка на статью", "Заголовок", "Редактор, автор")]

    try:
        news_items = soup.select(
            "#what-s-new-in-python div.toctree-wrapper li.toctree-l1"
        )

        for section in tqdm(news_items, desc="Обработка новостей"):
            try:
                version_a_tag = find_tag(section, "a")
                href = version_a_tag["href"]
                version_link = urljoin(whats_new_url, href)
                article_soup = fetch_and_parse(session, version_link)
                if not article_soup:
                    errors.append(f"Ошибка загрузки: {version_link}")
                    continue
                results.append(
                    (
                        version_link,
                        find_tag(article_soup, "h1").text,
                        find_tag(article_soup, "dl").text.replace("\n", " "),
                    )
                )

            except ParserFindTagException as e:
                errors.append(str(e))
                continue

    except ParserFindTagException as e:
        logging.error(str(e))
        return None

    for error in errors:
        logging.debug(error)

    return results


def latest_versions(session):
    """Парсит список всех версий Python."""
    soup = fetch_and_parse(session, MAIN_DOC_URL)
    if not soup:
        return None

    results = [("Ссылка на документацию", "Версия", "Статус")]
    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"

    try:
        version_links = soup.select(
            'div.sphinxsidebarwrapper ul:contains("All versions") a'
        )

        for link in tqdm(version_links, desc="Обработка версий"):
            try:
                text_match = re.search(pattern, link.text)
                version, status = (
                    text_match.groups() if text_match else (link.text, "")
                )
                results.append((version, status, link["href"]))
            except (KeyError, AttributeError) as e:
                logging.debug(LOG_SKIPP_VERSION.format(str(e)))
                continue

    except Exception as e:
        logging.error(LOG_PARSER_VERSION_ERROR.format(str(e)))
        return None

    return results


def download(session):
    """Скачивает архив с документацией Python в формате PDF."""
    soup = fetch_and_parse(session, urljoin(MAIN_DOC_URL, "download.html"))
    if not soup:
        return

    pdf_a4_tag = soup.select_one('table.docutils a[href$="pdf-a4.zip"]')

    if not pdf_a4_tag:
        raise ParserFindTagException("Не найдена ссылка на PDF архив")
    if "href" not in pdf_a4_tag.attrs:
        raise ParserFindTagException("У ссылки отсутствует атрибут href")

    archive_url = urljoin(MAIN_DOC_URL, pdf_a4_tag["href"])
    _download_file(session, archive_url, DOWNLOADS_DIR)


def _download_file(session, url, DOWNLOADS_DIR):
    """Вспомогательная функция для загрузки файла."""
    filename = url.split("/")[-1]
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    file_path = DOWNLOADS_DIR / filename

    try:
        response = session.get(url, stream=True)
        response.raise_for_status()
    except RequestException as e:
        error_msg = LOG_DOWNLOAD_ERROR.format(filename, str(e))
        logging.error(error_msg)
        raise ParserHTTPException(error_msg)

    total_size = int(response.headers.get("content-length", 0))
    logging.info(LOG_DOWNLOAD_START.format(filename))
    with open(file_path, "wb") as file:
        for chunk in tqdm(
            response.iter_content(chunk_size=1024),
            total=total_size // 1024 + 1,
            unit="KB",
            desc=filename,
            leave=True,
        ):
            if chunk:
                file.write(chunk)
    logging.info(LOG_ARCHIVE_SAVED.format(file_path))


def pep(session):
    """Анализирует статусы PEP."""
    soup = fetch_and_parse(session, PEP_URL)
    if not soup:
        return None

    status_counter = {}
    status_mismatches = []
    errors = []

    try:
        section = soup.select_one("section#numerical-index")
        rows = section.select("tbody tr")

        for row in tqdm(rows, desc="Обработка PEP"):
            try:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                status_abbr = cols[0].select_one("abbr")
                table_status = status_abbr["title"] if status_abbr else ""

                link_tag = cols[1].select_one("a")
                pep_url = urljoin(PEP_URL, link_tag["href"])
                print(pep_url)

                page_status = get_pep_status(session, pep_url)
                compare_statuses(
                    page_status, table_status, pep_url, status_mismatches
                )

                if page_status:
                    status_counter[page_status] = (
                        status_counter.get(page_status, 0) + 1
                    )

            except (ParserFindTagException, KeyError, AttributeError) as e:
                errors.append(f"{pep_url}: {str(e)}")
                continue

        for error in errors:
            logging.debug(LOG_SKIPP_PEP.format(error))

        return prepare_pep_results(status_counter, status_mismatches)

    except Exception as e:
        logging.error(LOG_CRITICAL_ERROR.format(str(e)))
        return None


def get_pep_status(session, pep_url):
    """Получает статус PEP со страницы."""
    try:
        soup = fetch_and_parse(session, pep_url)
        if not soup:
            return None

        status_tag = soup.find("dt", string="Status:").find_next_sibling("dd")
        return status_tag.text.strip() if status_tag else None

    except (ParserFindTagException, AttributeError) as e:
        logging.debug(LOG_RECIEVE_STATUS.format(pep_url, str(e)))
        return None


def compare_statuses(page_status, table_status, pep_url, mismatches):
    """Сравнивает статусы и сохраняет расхождения."""
    if not page_status or not table_status:
        return

    expected = EXPECTED_STATUS.get(table_status[0], [])
    if page_status not in expected:
        mismatches.append(
            {
                "url": pep_url,
                "page_status": page_status,
                "table_status": table_status,
            }
        )


def prepare_pep_results(counter, mismatches):
    """Формирует итоговые результаты."""
    results = [("Статус", "Количество")]
    total = sum(counter.values())
    results.extend(sorted(counter.items()))
    results.append(("Total", total))

    if mismatches:
        logging.info(LOG_STATUS_MISMATCH_HEADER)
        for m in mismatches:
            logging.info(LOG_STATUS_MISMATCH_ENTRY.format(**m))

    return results


MODE_TO_FUNCTION = {
    "whats-new": whats_new,
    "latest-versions": latest_versions,
    "download": download,
    "pep": pep,
}


def main():
    """Основная функция парсера с обработкой исключений."""
    try:
        configure_logging()
        logging.info(LOG_PARSER_START)

        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(LOG_ARGS_CMD.format(args))

        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()

        parser_mode = args.mode
        try:
            results = MODE_TO_FUNCTION[parser_mode](session)
            if results is not None:
                control_output(results, args)
        except Exception as e:
            logging.critical(
                LOG_CRITICAL_ERROR_IN_MODE.format(parser_mode, str(e)),
                exc_info=True,
            )
            raise

        logging.info(LOG_PARSER_STOP)

    except KeyboardInterrupt:
        logging.warning(LOG_PARSER_STOP_BY_USER)
    except Exception as e:
        logging.critical(LOG_UNEXPECTED_ERROR.format(str(e)), exc_info=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
