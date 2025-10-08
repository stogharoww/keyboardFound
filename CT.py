"""
Модуль для сравнительного анализа эргономики раскладок клавиатуры.
Загружает текстовые данные, инициализирует раскладки клавиатуры и проводит 
анализ эффективности различных раскладок для заданного текста.
"""

import numpy as np
import matplotlib as plt
import asyncio
import keyboardInit as keyb
import analization
import unicodedata


async def main():
    """
Основная асинхронная функция:
    - Загружает раскладки клавиатуры
    - Читает текстовые данные для анализа
    - Проводит сравнительный анализ раскладок
    - Выводит результаты
"""
    layouts = await keyb.keyInitializations()
    
    textFile = "data/voina-i-mir.txt"
    csvFile = "data/sortchbukw.csv"
    digrams = "data/1grams-3.txt"

    text, digrams, csvText = await keyb.importFromFiles(textFile, digrams, csvFile)
    text = unicodedata.normalize("NFC", text)
    
    analyzer = analization.TextAnalyzer(debug_mode=False)
    await analyzer.keybsInits()
    result = await analyzer.compareLayouts(text, analyzer.layouts)
    analyzer.returnResults(result)


if __name__ == '__main__':
    """Точка входа - запуск асинхронной main функции"""
    asyncio.run(main())
