# AGENTS.md

## Cursor Cloud specific instructions

Krepost — 4-слойный AI security pipeline (Python 3.12): чистая библиотека + demo HTTP API.
Стандартные команды — в `README.md` (разделы «Быстрый старт» и «Тесты»); ниже только
неочевидные для облачного окружения детали.

### Окружение
- Зависимости ставятся в изолированный `./.venv` (его создаёт update-скрипт). Пакет
  называется `krepost` — так же, как во втором репозитории воркспейса
  (`Krepost_Z.codeProject`), поэтому **общий venv невозможен**: у каждого репозитория свой.
- Установка тянет `torch` (транзитивно через `sentence-transformers`) — первый прогон
  долгий и объёмный; повторные быстрые.
- Запускайте инструменты как `.venv/bin/python` / `.venv/bin/pytest` (либо
  `source .venv/bin/activate`).

### Тесты
- `.venv/bin/pytest` — 201 тест, проходят без моделей и сети (guard/embedder мокаются).

### Запуск demo API
- `.venv/bin/python -m krepost.api.server` — FastAPI на `127.0.0.1:8000`
  (порт/хост переопределяются `KREPOST_API_PORT` / `KREPOST_API_HOST`).
- Это **modelless-демо** (`EchoBackend` + dev-guard, пропускающий всё как GREEN): реальные
  LLM/модели не нужны. Swagger UI — `/docs`, health — `/health`, метрики — `/metrics`.
- Проверка: `POST /v1/query {"text","session_id"}` — benign-запрос → `verdict=GREEN`,
  prompt-injection → `verdict=RED` (блок на `Layer1-Regex`).
- В воркспейсе есть второй сервис (`Krepost_Z.codeProject`); чтобы поднять оба сразу,
  задайте разные порты через `KREPOST_API_PORT`.
