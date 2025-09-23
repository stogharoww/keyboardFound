import numpy as np
import matplotlib as plt
import asyncio
import keyboardInit as keyb #структура данных раскладок
import analization


async def main():
    layouts = await keyb.keyInitializations()
    #print(layouts)
    textFile = "data/voina-i-mir.txt"
    csvFile = "data/sortchbukw.csv"
    digrams = "data/1grams-3.txt"

    algorithm = analization.TextAnalyzer()
    #await algorithm.importFromFiles()
    text, digrams, csvText = await keyb.importFromFiles(textFile, digrams, csvFile)


if __name__ == '__main__':
    asyncio.run(main())


