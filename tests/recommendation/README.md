# Recommendation Service — Тесты и инструкция по запуску

## 📘 Описание

Этот набор тестов предназначен для проверки **сервиса рекомендаций** (`recommendation`).  
Основная цель — убедиться, что публичный контракт сервиса корректен:  
методы вызываются без ошибок, возвращают данные в ожидаемом формате и устойчивы к временным сбоям внешних систем (Elastic, Redis, Mongo).

Тесты расположены в каталоге:
```
tests/recommendation/
```

### Что проверяют тесты

| Файл | Назначение |
|------|-------------|
| **`test_recommendation_service.py`** | Проверка базового контракта метода `get_recommendations`: возвращает список рекомендаций или `None`, не выбрасывает исключений, корректно обрабатывает разных пользователей. |
| **`test_cache_and_resilience.py`** | Проверка повторных вызовов и устойчивости к сбоям внешних систем (Elastic, Redis). Тест не измеряет скорость, а только гарантирует стабильность типа возвращаемых данных. |
| **`test_rank_weights.py`** | Проверка того, что сервис корректно обрабатывает разных пользователей без падений. Не фиксирует конкретную логику ранжирования или весов. |


## 🚀 Запуск тестов

Из корня репозитория:

```bash
# Активируйте виртуальное окружение
source .venv/bin/activate

# Убедитесь, что зависимости установлены
pip install -r requirements.txt

# Запустите все тесты recommendation
PYTHONPATH=$(pwd) pytest -q tests/recommendation
```

Вывод успешного запуска:
```
.....                                                                                              [100%]
```

---

## ⚠️ Предупреждения (Warnings)

При запуске могут появляться предупреждения вида:
- `DeprecationWarning: Passing transport options in the API method is deprecated`
- `DeprecationWarning: event_loop fixture has been redefined`

Это связано с особенностями тестового окружения (`conftest.py`) и не влияет на корректность тестов.  
Решение (опционально):
- перейти на `Elasticsearch.options()` вместо передачи параметров в `create/delete`;
- использовать `@pytest.mark.asyncio(scope="session")` вместо переопределения `event_loop`.

---

## 🧩 Структура проекта (фрагмент)

```
notifications_sprint_1/
├── recommendation/
│   └── src/
│       ├── main.py
│       └── services/
│           └── recomendation_service.py
├── tests/
│   └── recommendation/
│       ├── test_recommendation_service.py
│       ├── test_cache_and_resilience.py
│       └── test_rank_weights.py
├── requirements.txt
└── README.md
```

---



