"""
Модуль для сравнительного анализа эргономики раскладок клавиатуры.
Запускает полный анализ (текст, биграммы, CSV) и строит графики.
"""

import asyncio
import analization
from Graphics import GraphicsAnalyzer
import os


async def main():
    """
    Основная асинхронная функция для запуска полного анализа раскладок клавиатуры.

    Выполняет:
    1. Инициализацию анализатора текста
    2. Полный анализ всех корпусов данных
    3. Вывод результатов в консоль
    4. Построение графиков для каждого корпуса

    Returns:
        None
    """
    # Инициализация анализатора
    analyzer = analization.TextAnalyzer(debug_mode=False)

    # Запускаем полный анализ всех файлов (пути зашиты внутри)
    results_dict = await analyzer.run_full_analysis()

    # 🔍 Выводим результаты в консоль для каждого корпуса
    for corpus_name, raw_results in results_dict.items():
        print(f"\n===== Результаты для корпуса: {corpus_name} =====")
        for res in raw_results:
            layout_name, total_load, hand_switches, modifier_count, finger_stats, *rest = res
            word_stats = rest[0] if rest else None

            print(f"\n📋 Раскладка: {layout_name}")
            print(f"🔹 Общая нагрузка: {total_load}")
            print(f"🔹 Переключений рук: {hand_switches}")
            print(f"🔹 Модификаторов: {modifier_count}")
            print("🔹 Статистика по пальцам:")
            for finger, count in finger_stats.items():
                print(f"   {finger or 'None'}: {count}")

            if word_stats:
                print("🔹 Статистика по словам:")
                for k, v in word_stats.items():
                    print(f"   {k}: {v}")

    graphics = GraphicsAnalyzer(analyzer.layouts)

    # здесь мы знаем пути к файлам
    textFile = "data/voina-i-mir.txt"
    digramsFile = "data/digramms.txt"
    onegramsFile = "data/1grams-3.txt"
    csvFile = "data/sortchbukw.csv"

    # строим графики с названием файла в заголовке
    graphics.showAll(results_dict["text"], corpus_name=os.path.basename(textFile))
    graphics.showAll(results_dict["digramms"], corpus_name=os.path.basename(digramsFile))
    graphics.showAll(results_dict["onegramms"], corpus_name=os.path.basename(onegramsFile))
    graphics.showAll(results_dict["csv"], corpus_name=os.path.basename(csvFile))


if __name__ == '__main__':
   
    asyncio.run(main())
