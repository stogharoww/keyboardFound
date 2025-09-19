import numpy as np
import matplotlib as plt
import asyncio
import keyboardInit as keyb #структура данных раскладок
import analization


async def main():
    layouts = await keyb.keyInitializations()
    #print(layouts)
    textFile = "data/voina-i-mir.txt"
    analization.importFromFiles(textFile)


if __name__ == '__main__':
    asyncio.run(main())


