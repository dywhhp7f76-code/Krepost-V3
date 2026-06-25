# Предложение 07: Sovereign Execution Brokers

## Что

Архитектурный паттерн Sovereign Execution Broker — сертификат-привязанный контроль агентов. Каждый компонент Крепости (SecurityPipeline, SMART_CACHE, FewShotMatcher) получает криптографический сертификат, определяющий его полномочия. Брокер валидирует каждое действие перед исполнением.

## Зачем

1. **Принцип минимальных привилегий.** SecurityPipeline не должен иметь доступ к ChromaDB напрямую — только через FewShotMatcher. SMART_CACHE не должен модифицировать TrustRegistry. Сертификаты формализуют эти ограничения.

2. **Аудит действий.** Каждое действие подписано сертификатом компонента → невозможно отрицать, кто выполнил операцию. Интеграция с SecurityReceipt.

3. **Изоляция при компрометации.** Если атакующий обходит Layer 2, он получает доступ только к полномочиям GuardClassifier, а не ко всей системе.

4. **Горизонтальное масштабирование.** При добавлении новых компонентов (OCC-RAG reader, Threat Intelligence) каждый получает свой сертификат с явным набором разрешений.

## Что добавляется

| Файл | Назначение |
|------|------------|
| `krepost/security/broker.py` | Sovereign Execution Broker — валидация действий |
| `krepost/security/certs.py` | Генерация и управление сертификатами компонентов |
| `krepost/security/permissions.yaml` | Матрица разрешений: компонент → действие → ресурс |

### Пример матрицы разрешений

```yaml
components:
  SecurityPipeline:
    allowed:
      - action: "classify"
        resource: "user_input"
      - action: "read"
        resource: "regex_patterns"
      - action: "invoke"
        resource: "GuardClassifier"
      - action: "invoke"
        resource: "FewShotMatcher"
    denied:
      - action: "write"
        resource: "trust_registry"
      - action: "direct_access"
        resource: "chromadb"

  SMART_CACHE:
    allowed:
      - action: "read_write"
        resource: "cache_layers"
      - action: "read"
        resource: "embeddings"
    denied:
      - action: "modify"
        resource: "security_pipeline"
      - action: "access"
        resource: "trust_registry"
```

### Пример использования

```python
from krepost.security.broker import SovereignBroker

broker = SovereignBroker(permissions_path="permissions.yaml")

# Компонент запрашивает действие
result = broker.execute(
    caller_cert=pipeline_cert,
    action="invoke",
    resource="GuardClassifier",
    payload=user_input
)

if result.denied:
    logger.warning(f"[BROKER] Действие заблокировано: {result.reason}")
```

## Зависимости

| Зависимость | Назначение |
|-------------|------------|
| `cryptography` | Генерация X.509 сертификатов (уже в экосистеме Python) |
| `pyyaml` | Чтение матрицы разрешений |

## Риски

1. **Overhead.** Валидация каждого действия добавляет ~1-3ms. При 4 слоях pipeline — +4-12ms total. Приемлемо.
2. **Сложность начальной настройки.** Нужно определить полную матрицу разрешений для всех компонентов. Ошибка в матрице → блокировка легитимных операций (fail-closed).
3. **Ротация сертификатов.** Периодическая ротация добавляет operational complexity. Mitigation: auto-rotate с grace period.

## Статус: ⏳ Ожидает одобрения
