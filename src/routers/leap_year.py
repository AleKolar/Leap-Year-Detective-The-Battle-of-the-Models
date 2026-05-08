from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.services.leap_year_service import (
    is_leap_year, get_year_description, record_check,
    get_stats, get_celebrity
)

router = APIRouter(tags=["Leap Year"])

@router.get("/api/check/{year}")
async def check_year(year: int):
    leap = is_leap_year(year)
    description = get_year_description(year)
    record_check(year, leap)
    return JSONResponse({
        "year": year,
        "is_leap": leap,
        "description": description,
        "days": 366 if leap else 365,
        "celebrity": get_celebrity(year),
        "rule_check": {
            "divisible_by_4": year % 4 == 0,
            "divisible_by_100": year % 100 == 0,
            "divisible_by_400": year % 400 == 0,
            "exception_handled": True
        }
    })

@router.get("/api/stats")
async def stats():
    return get_stats()

@router.get("/api/famous-leaps")
async def famous_leaps():
    return {
        "history": {
            -45: "Юлий Цезарь ввел високосный год",
            1582: "Григорианская реформа календаря",
            1900: "Исключение — не високосный!",
            2000: "Миллениум и Y2K",
            2020: "Пандемия (но формальности соблюдены)",
            2024: "Текущий високосный год"
        },
        "celebrities": get_stats()["celebrity_birthdays"]
    }