# Парсер документации Python и PEP

## Автор проект
* [Alexander Batogov](https://github.com/Predatorevil666)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Парсер для сбора и анализа информации из документации Python и PEP (Python Enhancement Proposals).

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/bs4_parser_pep.git
cd bs4_parser_pep
```

    Установите зависимости:

```bash
pip install -r requirements.txt
```

## Использование
Основные команды
```bash
python src/main.py <режим> [аргументы]
```

## Доступные режимы

| Режим           | Описание                          |
|-----------------|-----------------------------------|
| whats-new       | Последние изменения в Python      |
| latest-versions | Доступные версии Python           |
| download        | Загрузка документации PDF         |
| pep             | Анализ статусов PEP               |

## Аргументы командной строки

| Аргумент               | Описание                          |
|------------------------|-----------------------------------|
| -h, help               | Общие сведения   
| -c, --clear-cache      | Очистка кеша                      |
| -o [pretty\|file]      | Формат вывода (консоль/файл)      |

## Примеры использования

### Показать нововведения с красивым выводом
```bash
python src/main.py whats-new -o pretty
```

### Проанализировать PEP и сохранить в файл
```bash
python src/main.py pep -o file
```
### Получить версии Python с очисткой кеша
```bash
python src/main.py latest-versions -c
```

## Структура проекта

```
bs4_parser_pep/
├── src/                   # Исходный код
│   ├── __init__.py
│   ├── configs.py         → Настройки парсера
│   ├── constants.py       → URL и константы
│   ├── exceptions.py      → Кастомные ошибки
│   ├── main.py           → Основная логика
│   ├── outputs.py         → Вывод результатов
│   └── utils.py           → Вспомогательные утилиты
├── tests/                 # Тесты
│   ├── fixture_data/      → Тестовые данные
│   └── test_*.py          → Модульные тесты
├── requirements.txt       → Зависимости
└── README.md              → Документация
```

## Технологии

    Python 3.10+

    BeautifulSoup4 - парсинг HTML/XML

    Requests + CachedSession - HTTP-запросы с кешированием

    PrettyTable - форматированный вывод таблиц

    pytest - тестирование

    Logging - логирование работы

## Примеры вывода

Режим whats-new (pretty output)

| Ссылка на статью                             | Заголовок                 | Редактор, автор          |
|-------------------------------------------   |-------------------------  |--------------------------|
| https://docs.python.org/3/whatsnew/3.10.html | What's New In Python 3.10 | Release 3.10.1, Editor: Pablo |
| https://docs.python.org/3/whatsnew/3.9.html  | What's New In Python 3.9  | Release 3.9.7            |

Режим pep (file output)

Создает CSV файл в папке results:
csv

| Статус   | Количество |
|----------|------------|
| Active   | 42         |
| Accepted | 15         |
| Final    | 30         |
| ...      | ...        |
| Total    | 574        |

## Разработка
Запуск тестов
```bash
pytest tests/
```



