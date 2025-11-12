"""
Модуль для сравнительного анализа эргономики раскладок клавиатуры.
Загружает текстовые данные, инициализирует раскладки клавиатуры и проводит 
анализ эффективности различных раскладок для заданного текста.
"""

import asyncio
import keyboardInit as keyb
import analization
import unicodedata
from Graphics import GraphicsAnalyzer   


async def main():
    textFile = "data/voina-i-mir.txt"
    csvFile = "data/sortchbukw.csv"
    digramsFile = "data/digramms.txt"

    # Загружаем данные
    text, digrams, csvText = await keyb.importFromFiles(textFile, digramsFile, csvFile)

    # Для анализа используем текст (или биграммы, если нужно)
    text = unicodedata.normalize("NFC", "".join(digrams))

    analyzer = analization.TextAnalyzer(debug_mode=False)
    await analyzer.keybsInits()

    # Запускаем сравнение раскладок
    result = await analyzer.compareLayouts(text, analyzer.layouts)
    structured = analyzer.returnResults(result)

    # 🔍 Выводим результат в консоль
    for layout in structured:
        print(f"\n📋 Раскладка: {layout['layout_name']}")
        print(f"🔹 Общая нагрузка: {layout['total_load']}")
        print(f"🔹 Переключений рук: {layout['hand_switches']}")
        print(f"🔹 Модификаторов: {layout['modifier_count']}")
        print("🔹 Статистика по пальцам:")
        for finger, count in layout['finger_statistics'].items():
            print(f"   {finger or 'None'}: {count}")

    # 📊 Вызов построения графиков
    graphics = GraphicsAnalyzer(analyzer.layouts)
    graphics.renderAll(result)  # 👈 сразу все графики


if __name__ == '__main__':
    asyncio.run(main())
