import asyncio
from backend.services.ai_service import find_duplicate_entities
async def test():
    entities = [
        {'id': 'likud', 'name_en': 'Likud'},
        {'id': 'likud_national_liberal_movement', 'name_en': 'Likud - National Liberal Movement'}
    ]
    res = await find_duplicate_entities(entities)
    print("RES:", res)

asyncio.run(test())
