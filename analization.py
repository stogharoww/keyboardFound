from keyboardInit import keyInitializations
import pandas as pd
import asyncio
import aiofiles


class TextAnalyzer:
    def __init__(self):
        """
        хз пробел, тут что-то надо чисто чтобы заполнить и всё. Если будет нужно, используйте
        """

    async def keybsInits(self):
        self.layouts = await keyInitializations()

    async def importFromFiles(self):
        """
        Загружает данные из файлов:
        - text: основной текст
        - csvText: строки из CSV-файла
        - digrams: таблица биграмм в формате pandas.DataFrame
        """
        async with aiofiles.open(self.textFile, "r", encoding="utf-8") as f:
            self.text = await f.read()

        async with aiofiles.open(self.digramsFile, "r", encoding="utf-8") as f:
            lines = await f.readlines()
            self.digrams = [line.strip() for line in lines]

        self.csvText = pd.read_csv(self.csvFile, header=None, sep=",")




    def getSymbolFinger(self, char: str, layout: dict) -> str:
        """
        Определяет, каким пальцем нажимается символ
        :param char: анализируемый символ
        :param layout: словарь раскладки с fingerKey
        :return: строка с идентификатором пальца (например, 'lfi2')
        """



    def getSumbolKey(self, char: str, layout: dict) -> str:
        """
        Определяет, на какой клавише находится символ
        :param char: анализируемый символ
        :param layout: словарь раскладки с bukvaKey
        :return: строка с индексом клавиши (например, '16')
        """

    def getModifierShtraf(self, char: str, layout: dict) -> int:
        """
        Проверяет, требует ли символ нажатия SHIFT или ALT, и возвращает соответствующий штраф
        :param char: анализируемый символ
        :param layout: словарь раскладки с modifierMap
        :return: целое число — сумма штрафов за модификаторы
        """

    def changeHand(self, char, previousChar):
        """
        сравнивает текущую и предыдущую руку, если r поменялось на l или наоборот, то +1 штраф
        :param char:
        :param previousChar:
        :return:
        """

    def calculateEffortSymbol(self, char: str, layout: dict, last_hand: dict) -> tuple[int, str]:
        """
        Суммирует все штрафы для символа:
        - за клавишу
        - за модификаторы
        - за смену руки
        :param char: анализируемый символ
        :param layout: словарь раскладки
        :param last_hand: словарь с последней активной рукой
        :return: кортеж (общий штраф, текущая рука)
        """

    def calculateEffortFinger(self, finger: str, layout: dict, calculateEffortSymb: dict):
        """
        Суммирует все штрафы по конкретному пальцу
        :param finger:
        :param layout:
        :param calculateEffortSymb:
        :return:
        """

    def analyzeText(self, text: str, layout: dict) -> dict:
        """
        Проходит по тексту и вычисляет:
        - общую нагрузку
        - нагрузку по пальцам
        - количество смен рук
        - количество модификаторов
        :param text: строка текста для анализа
        :param layout: словарь раскладки
        :return: словарь с результатами анализа
        """

    def compareLayouts(self, text: str, layouts: dict) -> dict:
        """
        Запускает анализы для каждой раскладки и текста и собирает сравнительную статистику,
        собирает значения для каждого пальца.
        Это финальная логическая функция, которая реально что-то считает
        :param text: строка текста для анализа
        :param layouts: словарь всех раскладок
        :return: словарь с результатами по каждой раскладке
        """

    def returnResults(self, result: dict) -> None:
        """
        Функция, которая создана исключительно только для вывода финальных результатов для графиков
        выводит нагрузки по каждому пальцу
        Форматирует и выводит результаты анализа:
        - нагрузка по пальцам
        - общая нагрузка
        - модификаторы
        - смены рук
        :param result: словарь с результатами анализа
        :return: None
        """
