# Krepost v3 — AI Security Pipeline

**Krepost** (Крепость) — 4-слойная система безопасности для локальных AI/LLM-систем.

Версия pipeline: **v2.2** | Версия cache: **v2.1** | Тесты: **104+**

> 📌 Изначальный замысел проекта (зачем всё это и какой баланс между
> свободой модели и контролем системы) зафиксирован в
> [ARCHITECTURE_VISION.md](./ARCHITECTURE_VISION.md).

---

## Архитектура

4-слойный security pipeline:

```
User → [Layer 1: Regex] → [Layer 2: Guard] → [Layer 3: FewShot] → LLM → [Layer 4: OutputFilter] → User
```

| Слой | Компонент | Описание |
|------|-----------|----------|
| 1 | **RegexFilter** | Нормализация Unicode, base64-decode, homoglyph detection, XML/CDATA, chat template injection |
| 2 | **GuardClassifier** | Семантический анализ через Qwen3Guard-Gen-4B, fail-closed, circuit breaker |
| 3 | **FewShotMatcher** | Cosine similarity через ChromaDB + BGE-M3, LRU cache, fail-closed |
| 4 | **OutputFilter** | PII masking (email, карты, ключи, IP, телефоны), leakage detection, Presidio (опц.) |

Принцип: **fail-closed** на каждом слое. Все sync-вызовы через `asyncio.to_thread`.

---

## Компоненты

### Security Pipeline v2.2
- 4 слоя защиты (Regex, Guard, FewShot, OutputFilter)
- Trust Registry (fast-path для доверенных запросов, SQLite)
- Unicode Normalization v2.2 (homoglyphs, zero-width, NFKC, BOM, BiDi)
- Rate limiting (token bucket), Circuit Breaker
- Audit hash и trace hash для каждого запроса

### Smart Cache v2.1
Трехслойный кэш:
- **L1 QueryEmbeddingCache** — exact match по SHA-256 хешу, O(1) lookup
- **L2 RAGResultsCache** — semantic match по cosine similarity (threshold 0.92)
- **L3 LLMResponseCache** — exact match по (query + context + model + prompt_version)

Безопасность кэша: L2/L3 сохраняют только запросы с verdict=GREEN. Anomaly detection (cache flood, high miss rate).

### Trust Registry
SQLite-based registry доверенных запросов. Нормализованные хеши, revoke support.

### Unicode Normalization
Единый модуль канонизации: homoglyph mapping (кириллица, греческий, цифры), zero-width removal, NFKC, casefold.

---

## Целевое оборудование

- **Mac Studio M4 Max 64GB** — основная модель + защита
- **MacBook Air M5 32GB** — атакующий (adversarial training)

## Модели

| Роль | Модель |
|------|--------|
| Основная | Qwen3.6-27B (Q4_K_M) |
| Guard | Qwen3Guard-Gen-4B |
| Embedder | BGE-M3 |

---

## Быстрый старт

```bash
# Установка
pip install -e .

# С поддержкой Presidio (PII detection)
pip install -e ".[presidio]"

# Dev-зависимости
pip install -e ".[dev]"

# Запуск тестов
pytest
```

### HTTP API (demo)

```bash
pip install -e ".[api]"
python -m krepost.api.server          # http://127.0.0.1:8000

curl -s localhost:8000/health
curl -s localhost:8000/v1/query \
  -H 'content-type: application/json' \
  -d '{"text":"напиши python код","session_id":"s1"}'
```

Обвязка поверх `Orchestrator`: `POST /v1/query` прогоняет запрос через
security → router → LLM → security и возвращает вердикт + ответ.
⚠️ Демо-сборка (`krepost.api.server`) использует dev-guard, пропускающий
всё — для прода нужен реальный Qwen3Guard и локальная LLM вместо EchoBackend.

---

## Структура проекта

```
Krepost-V3/
├── krepost/
│   └── security/
│       ├── pipeline.py          # Security Pipeline v2.2
│       ├── normalize.py         # Unicode normalization
│       └── trust_registry.py    # Trust Registry (SQLite)
├── src/krepost/
│   └── cache/
│       └── SMART_CACHE.py       # Smart Cache v2.1
├── tests/
│   ├── test_pipeline.py         # 66 тестов pipeline
│   ├── test_normalize.py        # 27 тестов нормализации
│   └── test_trust_registry.py   # 11 тестов trust registry
├── Krepost/                     # Obsidian knowledge base
│   ├── 01-ARCHITECTURE/
│   ├── 02-COMPONENTS/
│   ├── 03-ROADMAP/
│   └── ...
├── docs/                        # Документация
├── pyproject.toml
└── README.md
```

---

## Статус / Roadmap

### Фаза 0 — Текущая (без Mac)
- Выбор модели, security.py v1.1, промпты, Smart Cache v2.1, датасет

### Фаза 1 — Приход Mac (сборка)
- Соединение модулей, реальный Guard, инфраструктура, KVEraser, мониторинг

### Фаза 2 — После сборки
- Атакующий + adversarial training, Red Team Loop, self-improvement

---

## Тесты

104 теста, 3 файла:

```bash
pytest tests/ -v
```

Покрытие: SecurityContext, SecurityReceipt, RegexFilter (base64, homoglyphs, XML, CDATA, zero-width), GuardClassifier (parse, fail-closed), CircuitBreaker, RateLimiter, PIIMasker (email, карты Luhn, JWT, ключи, IP), OutputFilter, SecurityPipeline (integration), Unicode Normalization, Trust Registry.
