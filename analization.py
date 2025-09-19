from keyboardInit import keyInitializations as keyb
import pandas as pd
import asyncio
import aiofiles


class TextAnalyzer:
    def __init__(self, textFile, csvFile, digrams):
        """
        Инициализирует анализатор текста с путями к файлам:
        - textFile: путь к основному тексту для анализа
        - csvFile: путь к CSV-файлу с дополнительными данными (например, частотами)
        - digrams: путь к CSV-файлу с биграммами
        """
        self.textFile = textFile
        self.csvFile = csvFile
        self.digramsFile = digrams

    async def keybsInits(self):
        self.layouts = await keyb.keyboardInitialization()

    async def importFromFiles(self):
        """
        Загружает данные из файлов:
        - text: основной текст
        - csvText: строки из CSV-файла
        - digrams: таблица биграмм в формате pandas.DataFrame
        """
        async with aiofiles.open(self.textFile, "r", encoding="utf-8") as f:
            self.text = f.read()

        async with aiofiles.open(self.csvFile, "r", encoding="utf-8") as f:
            lines = await f.readlines()
            self.csvText = [line.strip() for line in lines]

        self.digrams = pd.read_csv(self.digramsFile, header=None)



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

    def calculateEffort(self, char: str, layout: dict, last_hand: dict) -> tuple[int, str]:
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
        Запускает analyzeText для каждой раскладки и собирает сравнительную статистику
        :param text: строка текста для анализа
        :param layouts: словарь всех раскладок
        :return: словарь с результатами по каждой раскладке
        """

    def returnResults(self, result: dict) -> None:
        """
        Форматирует и выводит результаты анализа:
        - нагрузка по пальцам
        - общая нагрузка
        - модификаторы
        - смены рук
        :param result: словарь с результатами анализа
        :return: None
        """
