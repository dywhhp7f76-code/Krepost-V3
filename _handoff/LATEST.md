# Журнал изменений для внешнего аудита

> Новые записи добавляются СВЕРХУ. Старые не удаляются и не редактируются.
> Строка «Проверка» — скопированный вывод команды, не пересказ.
> Конвенция: коммиты, меняющие ТОЛЬКО `_handoff/`, собственных записей
> не получают (иначе бесконечная рекурсия журнала о журнале).
> Журнал заведён 2026-07-01; записи ниже покрывают коммиты текущей сессии
> задним числом.

---

- fix: харденинг оркестрации после ревью — Route(keywords=[""]) перехватывал весь трафик (пустые keyword'ы теперь отбрасываются); CallableBackend не видел объекты с async __call__ (теперь детектит); +4 регрессионных теста
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/84d3a88fb5fab8a379234f93eddcda81120a582d
- Проверка: /tmp/verify_env/bin/python -m pytest Probnoki/test_21_orchestration.py -q → 20 passed in 4.91s; ruff check krepost/orchestration/ → All checks passed!; полный набор → 456 passed in 9.33s

---

- feat: слой оркестрации krepost/orchestration/ (Router + Orchestrator + бэкенды) — недостающее звено между security и LLM (ARCHITECTURE_VISION §4/§5.3); детерминированная маршрутизация, избирательный fail-closed (скомпрометированный вход → генерации нет; сбой бэкенда → мягкая деградация)
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/95b989b7c9cbe3da0175d3be1b2e1f4a18b78b4e
- Проверка: /tmp/verify_env/bin/python -m pytest Probnoki/test_21_orchestration.py -v → 16 passed in 96.65s; ruff check krepost/orchestration/ → All checks passed!; полный набор /tmp/verify_env/bin/python -m pytest tests/ Probnoki/ -q → 452 passed in 10.29s

---

## ИТОГ: PR #1 смержен в main (2026-07-01)

- feat: PR #1 (58 файлов: governance, Ataker-Boop, 8 фиксов безопасности, 20 пробников, 4 фикса внешнего аудита) смержен в main; ветка claude/repo-file-migration-3n3q50 перезапущена от нового main
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/fb3d97b38799a1aa1ae27c7df84dd50938d5b732
- Проверка: /tmp/verify_env/bin/pytest tests/ Probnoki/ -v (чистый venv, pip install -e ".[dev]" → Successfully installed ... krepost-2.2.0) → 436 passed in 11.63s; ruff check krepost/ → All checks passed! (полные выводы — в блоке верификации ниже)

---

## Аудит PR #1 — верификация в чистом venv (2026-07-01)

Статус 4 пунктов внешнего аудита:
- 1.1 глобальный lock в process()/process_output() — ПОДТВЕРЖДЁН, исправлен (lock только на проверке _closing)
- 1.2 numpy truthiness `if cached:` в FewShotMatcher.match() — ПОДТВЕРЖДЁН, исправлен (`if cached is not None:`)
- 1.3 пустая few-shot БД блокирует всё — ПОДТВЕРЖДЁН, исправлен (холодный старт = (False, [], None) + warning; fail-closed остался для аномалий/исключений)
- 1.4 build-backend "setuptools.backends._legacy:_Backend" — ПОДТВЕРЖДЁН, заменён на setuptools.build_meta; сверх задания добавлен явный packages.find (только корневой krepost/), иначе авто-дискавери падал на нескольких top-level пакетах / ставил устаревший дубликат src/krepost

Механическая верификация (шаг 2, чистый venv /tmp/verify_env):

```
$ /tmp/verify_env/bin/pip install -e ".[dev]"
EXIT=0
Successfully built krepost
Successfully installed MarkupSafe-3.0.3 ... chromadb-1.5.9 ... krepost-2.2.0
... numpy-2.4.6 ... pytest-9.1.1 pytest-asyncio-1.4.0 ... sentence-transformers-5.6.0
torch-2.12.1 transformers-5.12.1 ...  (полный список: 119 пакетов)

$ /tmp/verify_env/bin/python -c "import krepost; print(krepost.__file__)"
krepost from: /home/user/Krepost-V3/krepost/__init__.py

$ /tmp/verify_env/bin/pytest tests/ Probnoki/ -v   (последние строки вывода)
Probnoki/test_19_normalize_additions.py::TestMaxNormalizeLength::test_within_limit_passes PASSED [ 97%]
Probnoki/test_19_normalize_additions.py::TestMaxNormalizeLength::test_over_limit_raises PASSED [ 97%]
Probnoki/test_19_normalize_additions.py::TestMaxNormalizeLength::test_canonicalize_for_hash_over_limit_raises PASSED [ 98%]
Probnoki/test_19_normalize_additions.py::TestMaxNormalizeLength::test_pipeline_check_unaffected_by_new_guard PASSED [ 98%]
Probnoki/test_20_audit_fixes.py::TestNumpyTruthiness::test_repeat_query_same_verdict_with_ndarray PASSED [ 98%]
Probnoki/test_20_audit_fixes.py::TestNumpyTruthiness::test_second_call_uses_cache_not_encoder PASSED [ 98%]
Probnoki/test_20_audit_fixes.py::TestEmptyDbColdStart::test_empty_db_is_not_an_error PASSED [ 99%]
Probnoki/test_20_audit_fixes.py::TestEmptyDbColdStart::test_malformed_response_still_fail_closed PASSED [ 99%]
Probnoki/test_20_audit_fixes.py::TestEmptyDbColdStart::test_exception_still_fail_closed PASSED [ 99%]
Probnoki/test_20_audit_fixes.py::TestNoGlobalLockOnHotPath::test_concurrent_requests_run_in_parallel PASSED [ 99%]
Probnoki/test_20_audit_fixes.py::TestNoGlobalLockOnHotPath::test_process_after_close_still_raises PASSED [100%]
============================= 436 passed in 11.63s =============================
EXIT=0   (grep -c PASSED → 436)

$ ruff check krepost/          (после фикса F401)
All checks passed!

$ /tmp/verify_env/bin/pytest tests/ Probnoki/ -q   (повторный прогон после ruff-фиксов)
436 passed in 10.10s
EXIT=0
```

- refactor: убраны 7 замечаний ruff F401 (лишние импорты unicodedata/Enum/Dict/Optional; __all__ для re-export в governance/__init__.py)
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/86180270a1f706fca858f066e357b4264c1b5cf6
- Проверка: ruff check krepost/ → All checks passed!; /tmp/verify_env/bin/pytest tests/ Probnoki/ -q → 436 passed in 10.10s

- fix: 4 находки внешнего аудита — глобальный lock снят с горячего пути process()/process_output(); numpy truthiness в FewShotMatcher (`is not None`); пустая few-shot БД = холодный старт, не ошибка; build-backend → setuptools.build_meta + явный packages.find; добавлен пробник test_20_audit_fixes.py (7 тестов), обновлены 3 теста test_fewshot_matcher.py
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/3ad18857cd45c9b861e7294f78c9b74e2a3baa89
- Проверка: /tmp/verify_env/bin/pytest tests/ Probnoki/ -v → 436 passed in 11.63s (чистый venv, pip install -e ".[dev]" → Successfully installed ... krepost-2.2.0)

- feat: TaskContract — добавлены 3 инварианта честности dev-процесса (mechanical_check копируется без изменений; unchecked_example пустым быть не может; красный пробник запрещает VERIFIED)
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/a6c444b775fd8aa321e83d2d551be7f4696eb65c
- Проверка: python Probnoki/task_contract_draft.py → [T-042] accepted = True / [T-043] (нечестная сдача) accepted = False / ✗ unchecked_example пуст — заявлено полное покрытие (ложь) / ✗ check_command != mechanical_check — builder подогнал проверку (ждали: 'pytest tests/ -q')

- feat: черновик TaskContract в Probnoki/ — контракт передачи задач builder → 4 разнородных аудитора (A/B/C — не LLM, D — узкий чек-лист), ScopeGuard, VERIMAP
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/acbb8b439382632c15dc44da375e1928b2a387a0
- Проверка: python Probnoki/task_contract_draft.py → [T-042] accepted = True / [T-042] (после регресса) accepted = False / ✗ нарушение периметра scope: ['krepost/security/pipeline.py']

- docs: в README.md добавлена ссылка на ARCHITECTURE_VISION.md
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/7427c74f135bfa025d6321a31414bbdb74a5d7ae
- Проверка: НЕ ВЫПОЛНЯЛАСЬ (правка документации, исполняемого кода нет)

- docs: добавлен ARCHITECTURE_VISION.md — фиксация изначального замысла проекта (10 разделов: назначение, принципы, характер системы, связь с governance)
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/059d8b5cd2e8a75d9fdaf565a81e177d35a578b9
- Проверка: НЕ ВЫПОЛНЯЛАСЬ (новый документ, исполняемого кода нет)

- feat: normalize.py — ASCII fast-path и MAX_NORMALIZE_LENGTH guard (аддитивно, API не менялся; full-width записи в _HOMOGLYPH_MAP не добавлены — NFKC уже покрывает)
- Коммит: https://github.com/dywhhp7f76-code/Krepost-V3/commit/a12f37545c6aeb99b68bc0f0ad8f7ec504451717
- Проверка: python -m pytest Probnoki/test_19_normalize_additions.py -q → 14 passed in 2.36s
