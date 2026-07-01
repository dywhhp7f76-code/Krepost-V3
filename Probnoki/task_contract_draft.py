#!/usr/bin/env python3
"""
Черновик TaskContract — исполняемая схема контракта dev-задачи.

Статус: ЧЕРНОВИК в Probnoki/. Не импортируется основным кодом Крепости,
не трогает Layer 1-4. Это инструмент dev-процесса (builder → 4 аудитора),
а не рантайм-компонент.

Запуск как демо:
    python Probnoki/task_contract_draft.py

Что демонстрирует:
- схему TaskContract (dataclasses),
- разнородных аудиторов A/B/C/D (механизм, а не 4 копии LLM),
- gate: задача принята ТОЛЬКО если все 4 passed И пробник зелёный,
- возврат билдеру всегда с evidence (конкретный вывод инструмента).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
import fnmatch


# ─────────────────────────────────────────────────────────────────────────
# Схема
# ─────────────────────────────────────────────────────────────────────────

class Auditor(str, Enum):
    DETERMINISM = "A"   # запуск пробника, сверка хешей/выводов   (не LLM)
    STRUCTURE   = "B"   # AST + import-graph + grep: dead code    (не LLM)
    CONTRACT    = "C"   # валидация вывода builder против схемы    (не LLM)
    LOGIC       = "D"   # узкий чек-лист fail-closed/логики        (LLM)


@dataclass
class ScopeGuard:
    """Периметр правок. Прямая связка с правилом 'ничего не менять без согласия'."""
    allow: list[str] = field(default_factory=list)   # glob'ы, что можно
    forbid: list[str] = field(default_factory=list)  # glob'ы, что нельзя

    def violated_by(self, files_changed: list[str]) -> list[str]:
        """Возвращает файлы, нарушившие периметр (пусто = ок)."""
        bad = []
        for f in files_changed:
            if any(fnmatch.fnmatch(f, pat) for pat in self.forbid):
                bad.append(f)
                continue
            if self.allow and not any(fnmatch.fnmatch(f, pat) for pat in self.allow):
                bad.append(f)
        return bad


@dataclass
class Acceptance:
    """VERIMAP: пробник (код) + критерий (естественный язык). Пишется ДО builder."""
    probnik_path: str          # путь к исполняемому тесту-приёмке
    criterion_nl: str          # словесный критерий для аудитора D
    # Инъекция запуска пробника (в реале — subprocess pytest). Для демо — колбэк.
    run_probnik: Optional[Callable[[], bool]] = None

    def is_green(self) -> bool:
        return bool(self.run_probnik and self.run_probnik())


@dataclass
class Deliverable:
    """Что builder ОБЯЗАН вернуть, чтобы задачу вообще можно было проверять."""
    files_changed: list[str]
    api_unchanged: bool
    summary: str

    def is_complete(self) -> bool:
        return bool(self.files_changed) and bool(self.summary.strip())


@dataclass
class AuditVerdict:
    auditor: Auditor
    mechanism: str          # чем именно проверял
    passed: bool
    evidence: str           # вывод grep/теста/diff — НЕ «мне кажется»


@dataclass
class TaskContract:
    id: str
    goal: str
    scope: ScopeGuard
    acceptance: Acceptance
    deliverable: Optional[Deliverable] = None      # заполняет builder
    audit: list[AuditVerdict] = field(default_factory=list)

    # ── Gate ────────────────────────────────────────────────────────────
    def accepted(self) -> tuple[bool, list[str]]:
        """Задача принята ТОЛЬКО если всё сошлось. Возвращает (ok, причины_отказа)."""
        reasons: list[str] = []

        if self.deliverable is None:
            return False, ["builder не сдал deliverable"]

        if not self.deliverable.is_complete():
            reasons.append("deliverable неполный (нет files_changed или summary)")

        bad_files = self.scope.violated_by(self.deliverable.files_changed)
        if bad_files:
            reasons.append(f"нарушение периметра scope: {bad_files}")

        if not self.acceptance.is_green():
            reasons.append(f"пробник-приёмка красный: {self.acceptance.probnik_path}")

        seen = {v.auditor for v in self.audit}
        missing = [a.value for a in Auditor if a not in seen]
        if missing:
            reasons.append(f"нет вердикта от аудиторов: {missing}")

        for v in self.audit:
            if not v.passed:
                reasons.append(f"аудитор {v.auditor.value} завернул: {v.evidence}")

        return (len(reasons) == 0), reasons


# ─────────────────────────────────────────────────────────────────────────
# Демо: как это работает на реальном примере
# ─────────────────────────────────────────────────────────────────────────

def _demo() -> None:
    # 1. Оператор пишет контракт ДО builder. Пробник ещё красный.
    contract = TaskContract(
        id="T-042",
        goal="normalize.py: добавить ASCII fast-path, не сломав leetspeak-маппинг",
        scope=ScopeGuard(
            allow=["krepost/security/normalize.py", "Probnoki/**"],
            forbid=["krepost/security/pipeline.py"],   # этот файл трогать нельзя
        ),
        acceptance=Acceptance(
            probnik_path="Probnoki/test_19_normalize_additions.py",
            criterion_nl=(
                "ASCII-вход проходит быстрый путь, но casefold и confusables "
                "(0→o,1→i,5→s,|→i) всё ещё применяются; публичный API (str) не меняется."
            ),
            run_probnik=lambda: True,   # в реале: subprocess pytest -> exit 0
        ),
    )

    # 2. builder заполняет deliverable
    contract.deliverable = Deliverable(
        files_changed=["krepost/security/normalize.py",
                       "Probnoki/test_19_normalize_additions.py"],
        api_unchanged=True,
        summary="Добавлен isascii() fast-path + MAX_NORMALIZE_LENGTH guard.",
    )

    # 3-6. Четыре РАЗНОРОДНЫХ аудитора. Три из четырёх — не LLM.
    contract.audit = [
        AuditVerdict(Auditor.DETERMINISM, "pytest Probnoki/test_19 -q",
                     passed=True, evidence="14 passed in 0.12s"),
        AuditVerdict(Auditor.STRUCTURE, "grep full-width entries + AST unreachable",
                     passed=True, evidence="0 dead entries; full-width убран (NFKC покрывает)"),
        AuditVerdict(Auditor.CONTRACT, "проверка сигнатуры возврата == str",
                     passed=True, evidence="both funcs return str; api_unchanged=True подтверждён"),
        AuditVerdict(Auditor.LOGIC, "чек-лист: leetspeak сохранён? soft=True ветка? длина?",
                     passed=True, evidence="0/1/5/| маппинг проверен для ASCII-пути"),
    ]

    ok, reasons = contract.accepted()
    print(f"[{contract.id}] accepted = {ok}")
    for r in reasons:
        print(f"   ✗ {r}")

    # Контрпример: builder тронул запрещённый файл + один аудитор завернул
    contract.deliverable.files_changed.append("krepost/security/pipeline.py")
    contract.audit[1] = AuditVerdict(
        Auditor.STRUCTURE, "grep", passed=False,
        evidence="дубликат _HOMOGLYPH_MAP в src/krepost/ — рассинхрон")
    ok, reasons = contract.accepted()
    print(f"\n[{contract.id}] (после регресса) accepted = {ok}")
    for r in reasons:
        print(f"   ✗ {r}")


if __name__ == "__main__":
    _demo()
