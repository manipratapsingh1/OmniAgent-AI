import asyncio
from app.tools.calculator import calculator


def test_calculator():
    out = asyncio.run(calculator({"expression": "2+3*4"}))
    assert "= 14" in out