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
import argparse
import json

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="data/voina-i-mir.txt")
    parser.add_argument("--csv", default="data/sortchbukw.csv")
    parser.add_argument("--digrams", default="data/digramms.txt")
    parser.add_argument("--use-digrams", action="store_true")
    args = parser.parse_args()

    # Загружаем данные
    text, digrams, csvText = await keyb.importFromFiles(args.text, args.digrams, args.csv)

    # Выбираем источник текста
    if args.use_digrams:
        text = unicodedata.normalize("NFC", "".join(digrams))
    else:
        text = unicodedata.normalize("NFC", text)

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

    # 💾 Сохраняем результаты в JSON
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)

    # 📊 Вызов построения графиков
    graphics = GraphicsAnalyzer(analyzer.layouts)
    graphics.renderAll(result)

if __name__ == '__main__':
    asyncio.run(main())
