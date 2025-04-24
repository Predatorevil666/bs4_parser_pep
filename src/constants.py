from pathlib import Path

# URL-адреса
MAIN_DOC_URL = "https://docs.python.org/3/"
PEP_URL = "https://peps.python.org/numerical/"

# Пути и директории
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "parser.log"
RESULTS_DIR = BASE_DIR / "results"
DOWNLOADS_DIR = BASE_DIR / "downloads"

# Форматы даты и времени
DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
DT_FORMAT = "%d.%m.%Y %H:%M:%S"

# Настройки логирования
LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
MAX_BYTES = 10**6
BACKUP_COUNT = 5

# Параметры вывода
PRETTY_OUTPUT = "pretty"
FILE_OUTPUT = "file"


# Статусы PEP
EXPECTED_STATUS = {
    "A": ("Active", "Accepted"),
    "D": ("Deferred",),
    "F": ("Final",),
    "P": ("Provisional",),
    "R": ("Rejected",),
    "S": ("Superseded",),
    "W": ("Withdrawn",),
    "": ("Draft", "Active"),
}


# Константы логирования
LOG_PARSER_START = "Парсер PEP запущен"
LOG_PARSER_STOP = "Парсер PEP завершил работу"
LOG_ARGS_CMD = "Аргументы командной строки: {}"
LOG_ARCHIVE_SAVED = "Архив был загружен и сохранён: {}"
LOG_STATUS_MISMATCH_HEADER = "Несовпадающие статусы:"
LOG_STATUS_MISMATCH_ENTRY = (
    "URL: {url}\nСтатус на странице:"
    " {page_status}\nСтатус в таблице: {table_status}"
)
LOG_SKIPP_VERSION = "Пропущена версия: {}"
LOG_SKIPP_PEP = "Пропуск PEP: {}"
LOG_PARSER_VERSION_ERROR = "Ошибка при парсинге версий: {}"
LOG_DOWNLOAD_START = "Начата загрузка файла: {}"
LOG_DOWNLOAD_ERROR = "Ошибка при загрузке {}: {}"
LOG_CRITICAL_ERROR = "Критическая ошибка: {}"
LOG_CRITICAL_ERROR_IN_MODE = "Критическая ошибка в режиме '{}': {}"
LOG_PARSER_STOP_BY_USER = "Работа парсера прервана пользователем"
LOG_UNEXPECTED_ERROR = "Непредвиденная ошибка: {}"
LOG_RECIEVE_STATUS = "Ошибка получения статуса {}: {}"
LOG_FILE_SAVED = "Файл с результатами был сохранён: {}"
