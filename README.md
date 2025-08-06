## BotGetCert
[![Version](https://img.shields.io/badge/version-v2.5-blue)](https://github.com/nihosprop/bot_get_cert.git)
[![Python](https://img.shields.io/badge/Python-3.13.1-green)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.21-brightgreen)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Redis](https://img.shields.io/badge/Redis-7-red)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-20.10%2B-blue)](https://www.docker.com/)
<div align="center">
  <a href="https://t.me/certificates7_bot">
    <img src="https://img.icons8.com/clouds/100/000000/telegram-app.png" 
width="100"/>
    <br>
    <strong>🚀 Протестировать бота BotGetCert</strong>
  </a>
</div>

✨ Возможности

- **Автоматическая генерация** сертификатов PDF/PNG
- **Интеграция с Stepik API**:
  - Проверка завершения курса
  - Получение данных студента
- **Персонализация**:
  - Подпись преподавателяЛЛ
- **Управление через Telegram**:
  - Запрос сертификата
  - История выданных документов

## 🛠 Технологический стек

| Компонент          | Назначение                                   |
|--------------------|----------------------------------------------|
| **Python 3.13+**   | Основной язык разработки                     |
| **Aiogram**        | Telegram Bot Framework                       |
| **PostgreSQL**     | Хранение данных сертификатов и пользователей |
| **SQLAlchemyORM**  | Работа с PostgreSQL по средствам ООП         |
| **PyPDF2**      | Генерация PDF-сертификатов                   |
| **Pillow**         | Создание графических сертификатов (PNG)      |
| **Docker**         | Контейнеризация                              |
| **Stepik API**     | Интеграция с образовательной платформой      |
| **GitHub Actions** | CI/CD: автотесты и деплой на DockerHub       |

## 🚀 Быстрый старт

```bash

# Клонирование репозитория
git clone https://github.com/nihosprop/bot_get_cert.git
```
Структура проекта
```
your_name_bot_dir
├── data
│  ├── 1 часть жен.pdf
│  ├── 1 часть муж.pdf
│  └── Bitter-Regular.ttf
├── docker-compose.yml
├── logs
│  └── logging_setting
│    └── log_config.yml
└── redis.conf
├── .env
```

Деплой через docker-composePROD

```code
1. Прописать docker-compose.yml заменив данные на свои.

2. Прописать .env по аналогии .env.example, заменив данные на свои

2. Прописать redis.conf под свои нужды..

! Задать пароль для Redis в .env и redis.conf
! Redis пароли должны совпадать в .env и redis.conf
```

Находясь в корне проекта(бота) исполнить:
```code
docker compose up -d
```
