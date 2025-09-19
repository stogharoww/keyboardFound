import numpy as np
import matplotlib as plt
import asyncio
import keyboardInit as keyb #структура данных раскладок



def importFiles(text, lexemes, digrams):
    """

    :param text: Война и мир
    :param lexemes: лексемы русского языка
    :param digrams: CSV файл
    :return:
    """


def fingerLoads(text: str, keyboards):
    """

    :param text:
    :param keyboards:
    :return:
    """

def keyboardCompare(loadsFinger):
    """
    :param loadsFinger: Словарь: раскладка -> нагрузка по пальцам
    :return:
    """



async def main():
    layouts = await keyb.keyInitializations()
    print(layouts)



if __name__ == '__main__':
    asyncio.run(main())


