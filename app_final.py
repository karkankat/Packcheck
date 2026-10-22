"""PackCheck — сервис проверки снаряжения для велопохода.

Учебная основа: app_final.py из материалов курса.
"""

import logging
import math
import os

from fastapi import FastAPI, Query


APP_VERSION = "0.3.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("packcheck")

try:
    DEFAULT_WEIGHT_LIMIT_KG = float(os.getenv("DEFAULT_WEIGHT_LIMIT_KG", "10"))
except ValueError:
    raise ValueError(
        "DEFAULT_WEIGHT_LIMIT_KG должна содержать число, например 10 или 8.5"
    ) from None

if (
    not math.isfinite(DEFAULT_WEIGHT_LIMIT_KG)
    or DEFAULT_WEIGHT_LIMIT_KG <= 0
    or DEFAULT_WEIGHT_LIMIT_KG != round(DEFAULT_WEIGHT_LIMIT_KG, 3)
):
    raise ValueError(
        "DEFAULT_WEIGHT_LIMIT_KG должна быть положительным числом "
        "с точностью до 0.001 кг"
    )

app = FastAPI(title="PackCheck", version=APP_VERSION)

logger.info(
    "Настройки PackCheck: version=%s default_limit_kg=%s",
    APP_VERSION,
    DEFAULT_WEIGHT_LIMIT_KG,
)

GEAR = [
    {"id": 1, "name": "Палатка", "category": "sleep", "weight_g": 1500},
    {"id": 2, "name": "Спальник", "category": "sleep", "weight_g": 1000},
    {"id": 3, "name": "Коврик", "category": "sleep", "weight_g": 500},
    {"id": 4, "name": "Мультитул", "category": "repair", "weight_g": 200},
    {"id": 5, "name": "Насос", "category": "repair", "weight_g": 150},
    {"id": 6, "name": "Дождевик", "category": "clothes", "weight_g": 300},
    {"id": 7, "name": "Запасная одежда", "category": "clothes", "weight_g": 750},
    {"id": 8, "name": "Вода", "category": "supplies", "weight_g": 2500},
    {"id": 9, "name": "Еда", "category": "supplies", "weight_g": 1500},
]


def get_total_weight_g():
    total_weight = 0
    for item in GEAR:
        total_weight += item["weight_g"]
    return total_weight


@app.get("/")
def root():
    return {"message": "PackCheck работает", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": APP_VERSION}


@app.get("/items")
def items(category: str | None = None):
    selected_items = []
    for item in GEAR:
        if category is None or item["category"] == category:
            selected_items.append(item)
    return {"item_count": len(selected_items), "items": selected_items}


@app.get("/summary")
def summary():
    total_weight_g = get_total_weight_g()
    heaviest_item = None
    for item in GEAR:
        if heaviest_item is None or item["weight_g"] > heaviest_item["weight_g"]:
            heaviest_item = item
    return {
        "item_count": len(GEAR),
        "total_weight_g": total_weight_g,
        "total_weight_kg": total_weight_g / 1000,
        "heaviest_item": heaviest_item,
    }


@app.get("/check")
def check(
    limit_kg: float = Query(
        default=DEFAULT_WEIGHT_LIMIT_KG,
        gt=0,
        multiple_of=0.001,
        allow_inf_nan=False,
        description="Положительный лимит веса в кг с точностью до 0.001 кг",
    ),
):
    total_weight_kg = get_total_weight_g() / 1000
    fits = total_weight_kg <= limit_kg
    logger.info(
        "Проверка веса: total_kg=%.3f limit_kg=%.3f fits=%s",
        total_weight_kg,
        limit_kg,
        fits,
    )
    return {
        "total_weight_kg": total_weight_kg,
        "limit_kg": limit_kg,
        "fits": fits,
        "remaining_kg": round(max(0.0, limit_kg - total_weight_kg), 3),
        "overweight_kg": round(max(0.0, total_weight_kg - limit_kg), 3),
    }