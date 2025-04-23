import logging
import re

from urllib.parse import urljoin

import requests_cache

from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, PEP_URL
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")
    response = get_response(session, whats_new_url)
    soup = BeautifulSoup(response.text, "lxml")
    news = find_tag(soup, "div", attrs={"class": "toctree-wrapper compound"})
    news_link = news.find_all("li", attrs={"class": "toctree-l1"})
    results = [("Ссылка на статью", "Заголовок", "Редактор, автор")]
    for section in tqdm(news_link):
        version_a_tag = find_tag(section, "a")
        href = version_a_tag["href"]
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        soup = BeautifulSoup(response.text, "lxml")
        h1 = find_tag(soup, "h1")
        dl = find_tag(soup, "dl")
        dl_text = dl.text.replace("\n", " ")
        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    soup = BeautifulSoup(response.text, "lxml")
    sidebar = find_tag(soup, "div", {"class": "sphinxsidebarwrapper"})
    ul_tags = sidebar.find_all("ul")
    for ul in ul_tags:
        if "All versions" in ul.text:
            a_tags = ul.find_all("a")
            break
    else:
        raise Exception("Ничего не нашлось")
    results = [("Ссылка на документацию", "Версия", "Статус")]
    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"
    for a_tag in a_tags:
        link = a_tag["href"]
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ""
        results.append((link, version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, "download.html")
    response = get_response(session, downloads_url)
    soup = BeautifulSoup(response.text, "lxml")
    table_tag = soup.find("table", attrs={"class": "docutils"})
    table_tag = find_tag(soup, "table", attrs={"class": "docutils"})
    pdf_a4_tag = find_tag(
        table_tag, "a", {"href": re.compile(r".+pdf-a4\.zip$")}
    )
    pdf_a4_link = pdf_a4_tag["href"]
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split("/")[-1]
    downloads_dir = BASE_DIR / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    with open(archive_path, "wb") as file:
        for chunk in tqdm(
            response.iter_content(chunk_size=1024),
            total=total_size // 1024 + 1,
            unit="KB",
            desc=filename,
            leave=True,
        ):
            if chunk:
                file.write(chunk)
    logging.info(f"Архив был загружен и сохранён: {archive_path}")


def pep(session):
    """Основная функция парсинга статусов PEP."""
    response = get_response(session, PEP_URL)
    if not response:
        return None

    soup = BeautifulSoup(response.text, "lxml")

    try:
        tables = soup.find_all(
            "table", class_="pep-zero-table docutils align-default"
        )
        if not tables:
            raise ParserFindTagException("Не найдены таблицы с PEP")

        status_counter = {}
        status_mismatches = []

        for table in tables:
            process_pep_table(
                table, session, status_counter, status_mismatches
            )

        return prepare_results(status_counter, status_mismatches)

    except ParserFindTagException as e:
        logging.error(str(e))
        return None


def process_pep_table(table, session, status_counter, status_mismatches):
    """Обрабатывает одну таблицу с PEP."""
    rows = table.find_all("tr")[1:]

    for row in tqdm(rows, desc="Обработка PEP"):
        try:
            process_pep_row(row, session, status_counter, status_mismatches)
        except (ParserFindTagException, KeyError) as e:
            logging.debug(f"Пропуск PEP: {str(e)}")
            continue


def process_pep_row(row, session, status_counter, status_mismatches):
    """Обрабатывает одну строку с PEP."""
    cols = row.find_all("td")
    if len(cols) < 3:
        return

    try:
        status_abbr = cols[0].find("abbr", attrs={"title": True})
        if not status_abbr:
            logging.debug(f"Пропуск строки без тега abbr: {row.text.strip()}")
            return
        pep_link_tag = cols[1].find("a", href=True)
        if not pep_link_tag:
            logging.debug(f"Пропуск строки без ссылки: {row.text.strip()}")
            return

        pep_link = urljoin(PEP_URL, pep_link_tag["href"])
        page_status = get_pep_page_status(session, pep_link)

        if page_status:
            table_status = status_abbr["title"]
            if not compare_statuses(page_status, table_status):
                status_mismatches.append(
                    {
                        "url": pep_link,
                        "page_status": page_status,
                        "table_status": table_status,
                    }
                )
            status_counter[page_status] = (
                status_counter.get(page_status, 0) + 1
            )

    except Exception as e:
        logging.debug(f"Ошибка обработки строки: {str(e)}")


def get_pep_page_status(session, pep_url):
    """Получает статус PEP со страницы с обработкой ошибок."""
    response = get_response(session, pep_url)
    if not response:
        return None

    try:
        soup = BeautifulSoup(response.text, "lxml")
        for dt in soup.find_all("dt"):
            if dt.get_text(strip=True) == "Status:":
                dd = dt.find_next_sibling("dd")
                return dd.get_text(strip=True) if dd else None
        return None
    except Exception as e:
        logging.debug(f"Ошибка парсинга страницы {pep_url}: {str(e)}")
        return None


def compare_statuses(page_status, table_status):
    """Сравнивает статусы со страницы и из таблицы."""
    page_normalized = page_status.lower().strip()
    table_normalized = table_status.lower().strip()
    return (
        page_normalized in table_normalized
        or table_normalized in page_normalized
        or any(
            part.strip() == page_normalized
            for part in table_normalized.split(",")
        )
    )


def prepare_results(status_counter, status_mismatches):
    """Формирует итоговые результаты."""
    if status_mismatches:
        log_status_mismatches(status_mismatches)
    results = [("Статус", "Количество")]
    total = sum(status_counter.values())
    for status, count in sorted(status_counter.items()):
        results.append((status, count))
    results.append(("Total", total))
    return results


def log_status_mismatches(mismatches):
    """Логирует несовпадающие статусы."""
    logging.info("Несовпадающие статусы:")
    for mismatch in mismatches:
        logging.info(
            f"{mismatch['url']}\n"
            f"Статус на странице: {mismatch['page_status']}\n"
            f"Статус в таблице: {mismatch['table_status']}\n"
        )


MODE_TO_FUNCTION = {
    "whats-new": whats_new,
    "latest-versions": latest_versions,
    "download": download,
    "pep": pep,
}


def main():
    configure_logging()
    logging.info("Парсер PEP запущен")

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f"Аргументы командной строки: {args}")

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)

    logging.info("Парсер PEP завершил работу")


if __name__ == "__main__":
    main()
