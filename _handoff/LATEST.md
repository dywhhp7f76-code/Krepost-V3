# Журнал изменений для внешнего аудита

> Новые записи добавляются СВЕРХУ. Старые не удаляются и не редактируются.
> Строка «Проверка» — скопированный вывод команды, не пересказ.
> Конвенция: коммиты, меняющие ТОЛЬКО `_handoff/`, собственных записей
> не получают (иначе бесконечная рекурсия журнала о журнале).
> Журнал заведён 2026-07-01; записи ниже покрывают коммиты текущей сессии
> задним числом.

---

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
