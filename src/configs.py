import argparse
import logging

from logging.handlers import RotatingFileHandler

from constants import (
    BACKUP_COUNT,
    DT_FORMAT,
    FILE_OUTPUT,
    LOG_DIR,
    LOG_FILE,
    LOG_FORMAT,
    MAX_BYTES,
    PRETTY_OUTPUT,
)


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(
        description="Парсер документации Python и PEP"
    )
    parser.add_argument(
        "mode", choices=available_modes, help="Режимы работы парсера"
    )
    parser.add_argument(
        "-c", "--clear-cache", action="store_true", help="Очистка кеша"
    )
    parser.add_argument(
        "-o",
        "--output",
        choices=(PRETTY_OUTPUT, FILE_OUTPUT),
        help="Дополнительные способы вывода данных",
    )
    return parser


def configure_logging():
    LOG_DIR.mkdir(exist_ok=True)
    rotating_handler = RotatingFileHandler(
        LOG_FILE, MAX_BYTES, BACKUP_COUNT, encoding="utf-8"
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler()),
    )
