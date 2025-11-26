import matplotlib.pyplot as plt
import numpy as np


class GraphicsAnalyzer:
    """
    КЛАСС ДЛЯ СОЗДАНИЯ ГРАФИКОВ - превращает скучные цифры в красивые диаграммы.
    Как художник, который рисует картины по результатам анализа клавиатур.
    """

    def __init__(self, layouts: dict):
        """
        Настраивает художника-графика.

        layouts - словарь с раскладками клавиатур (чтобы знать, что рисовать)
        """
        # Словарь с раскладками, которые будем анализировать
        self.layouts = layouts

        # Цвета для каждой раскладки (чтобы на графиках отличались)
        self.layout_colors = {
            "qwerty": "red",  # раскладка йцукен - красный
            "yaverty": "purple",  # раскладка яверты - фиолетовый
            "vizov": "black"  # раскладка вызов - черный
        }

        # Русские названия для подписей на графиках
        self.layout_labels = {
            "qwerty": "йцукен",
            "vizov": "вызов",
            "yaverty": "яверты"
        }

        # Русские названия для пальцев (чтобы было понятно)
        self.finger_names_ru = {
            'lfi5': 'Левый мизинец',
            'lfi4': 'Левый безымянный',
            'lfi3': 'Левый средний',
            'lfi2': 'Левый указательный',
            'lfi1': 'Левый большой',
            'rfi1': 'Правый большой',
            'rfi2': 'Правый указательный',
            'rfi3': 'Правый средний',
            'rfi4': 'Правый безымянный',
            'rfi5': 'Правый мизинец'
        }

        # Порядок пальцев на графиках (слева направо)
        self.finger_order = ['lfi5', 'lfi4', 'lfi3', 'lfi2', 'lfi1',
                             'rfi1', 'rfi2', 'rfi3', 'rfi4', 'rfi5']

    def _normalize_name(self, name: str) -> str:
        """
        Приводит названия раскладок к единому стандарту.
        Как переводчик - переводит разные названия в один язык.
        """
        # Убираем лишние пробелы и переводы строк
        clean = name.strip().lower().replace("\n", "").replace("\r", "")

        # Словарь для перевода разных названий
        mapping = {
            "йцукен": "qwerty",
            "qwerty": "qwerty",
            "яверты": "yaverty",
            "yaverty": "yaverty",
            "vizov": "vizov",
            "вызов": "vizov"
        }
        return mapping.get(clean, clean)

    def _prepare_results(self, results: list) -> tuple[list, list]:
        """
        Подготавливает результаты для построения графиков.
        Как повар подготавливает ингредиенты перед готовкой.
        """
        structured = []  # аккуратно упакованные результаты
        all_layouts_data = []  # данные по всем раскладкам

        # Обрабатываем каждый результат
        for res in results:
            # Если результат в словаре - берем данные оттуда
            if isinstance(res, dict):
                layout_name = res["layout_name"]
                total_load = res["total_load"]
                hand_switches = res["hand_switches"]
                modifier_count = res["modifier_count"]
                finger_stats = res["finger_statistics"]
                word_stats = res.get("word_stats")
            else:
                # Если результат в списке - распаковываем
                if len(res) == 6:
                    layout_name, total_load, hand_switches, modifier_count, finger_stats, word_stats = res
                else:
                    layout_name, total_load, hand_switches, modifier_count, finger_stats = res
                    word_stats = None

            # Заполняем нулями отсутствующие пальцы
            all_fingers = set(self.layouts[layout_name]["fingerKey"].keys())
            for f in all_fingers:
                if f not in finger_stats:
                    finger_stats[f] = 0

            # Упаковываем в удобный формат
            structured.append({
                "layout_name": layout_name,
                "total_load": total_load,
                "hand_switches": hand_switches,
                "modifier_count": modifier_count,
                "finger_statistics": finger_stats,
                "word_stats": word_stats
            })

            # Сохраняем данные для графиков
            all_layouts_data.append({
                "name": layout_name,
                "stats": finger_stats,
                "total": total_load,
                "hand_switches": hand_switches,
                "modifier_count": modifier_count,
                "word_stats": word_stats
            })

        return structured, all_layouts_data

    # ---------------- ГРАФИКИ ----------------

    def _create_all_layouts_comparison_chart(self, layouts_data: list, corpus_name: str):
        """
        Рисует большой график сравнения нагрузки на пальцы для всех раскладок.
        Как столбиковая диаграмма, где видно, какие пальцы работают больше.
        """
        if not layouts_data:
            return

        # Готовим названия пальцев на русском
        fingers = [self.finger_names_ru.get(f, f) for f in self.finger_order]
        y_pos = np.arange(len(fingers))
        bar_height = 0.2  # высота столбиков
        fig, ax = plt.subplots(figsize=(14, 6))

        # Рисуем столбики для каждой раскладки
        for i, layout_data in enumerate(layouts_data):
            alias = self._normalize_name(layout_data["name"])
            layout_color = self.layout_colors.get(alias, 'gray')
            label = self.layout_labels.get(alias, layout_data["name"])
            values = [layout_data["stats"].get(f, 0) for f in self.finger_order]

            # Смещаем столбики, чтобы не накладывались
            offset = (i - (len(layouts_data) - 1) / 2) * bar_height
            bars = ax.barh(y_pos + offset, values, height=bar_height,
                           color=layout_color, alpha=0.7, label=label)

            # Добавляем проценты на столбики
            total = sum(values)
            max_val = max(values) if values else 1
            for bar, value in zip(bars, values):
                percent = value / total * 100 if total else 0
                width = bar.get_width()
                ax.text(width + max_val * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f'{percent:.1f}%',
                        ha='left', va='center', fontsize=8)

        # Настраиваем внешний вид графика
        ax.set_yticks(y_pos)
        ax.set_yticklabels(fingers, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel('Нагрузка (единицы пути)', fontsize=12)
        ax.set_title(f'Сравнение нагрузки по пальцам ({corpus_name})',
                     fontsize=14, fontweight='bold')
        ax.legend()

        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        plt.tight_layout()
        plt.show()

    def _create_total_load_chart(self, layouts_data: list, corpus_name: str):
        """
        Рисует простой график общей нагрузки по раскладкам.
        Показывает, какая раскладка в целом удобнее (меньше нагрузка).
        """
        # Собираем названия и общую нагрузку
        names = [layout["name"] for layout in layouts_data]
        totals = [layout["total"] for layout in layouts_data]

        fig, ax = plt.subplots(figsize=(14, 2.5))
        y_pos = np.arange(len(names))

        # Подбираем цвета и русские названия
        colors = [self.layout_colors.get(self._normalize_name(name), 'gray') for name in names]
        labels = [self.layout_labels.get(self._normalize_name(name), name) for name in names]
        bars = ax.barh(y_pos, totals, color=colors, alpha=0.7)

        # Настраиваем подписи
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=11)
        ax.set_xlabel('Общая нагрузка (единицы пути)', fontsize=12)
        ax.set_title(f'Общая нагрузка по раскладкам ({corpus_name})',
                     fontsize=14, fontweight='bold')

        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()

    def _create_hand_distribution_chart(self, layouts_data: list, corpus_name: str):
        """
        Рисует график распределения нагрузки между левой и правой рукой.
        Показывает, какая рука работает больше.
        """
        names = [layout["name"] for layout in layouts_data]
        left_loads, right_loads = [], []

        # Считаем нагрузку отдельно для левой и правой руки
        for layout in layouts_data:
            left_load = sum(v for k, v in layout["stats"].items() if k.startswith('l'))
            right_load = sum(v for k, v in layout["stats"].items() if k.startswith('r'))
            left_loads.append(left_load)
            right_loads.append(right_load)

        y = np.arange(len(names))
        height = 0.35  # высота столбиков

        fig, ax = plt.subplots(figsize=(14, 2.5))

        colors = [self.layout_colors.get(self._normalize_name(name), 'gray') for name in names]
        labels = [self.layout_labels.get(self._normalize_name(name), name) for name in names]

        # Рисуем два столбика для каждой раскладки: левая и правая рука
        ax.barh(y - height / 2, left_loads, height,
                label='Левая рука', color=colors, alpha=0.7)
        ax.barh(y + height / 2, right_loads, height,
                label='Правая рука', color=colors, alpha=0.4)

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=11)
        ax.set_xlabel('Нагрузка (единицы пути)', fontsize=12)
        ax.set_title(f'Распределение нагрузки между руками ({corpus_name})',
                     fontsize=14, fontweight='bold')
        ax.legend()

        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()

    def _create_hand_pie_charts(self, layouts_data: list, corpus_name: str):
        """
        Рисует круговые диаграммы: какие слова печатаются одной рукой, а какие двумя.
        Показывает распределение слов по рукам.
        """
        n_layouts = len(layouts_data)
        if n_layouts == 0:
            return

        # Решаем, сколько строк и столбцов нужно для диаграмм
        cols = min(2, n_layouts)
        rows = (n_layouts + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
        fig.suptitle(f'Круговые диаграммы распределения слов по рукам ({corpus_name})',
                     fontsize=16, fontweight='bold')

        # Настраиваем оси для разных случаев
        if n_layouts == 1:
            axes = np.array([axes])
        if rows == 1 and cols == 1:
            axes = np.array([axes])
        elif rows == 1:
            axes = axes.reshape(1, -1)
        elif cols == 1:
            axes = axes.reshape(-1, 1)

        # Рисуем круговую диаграмму для каждой раскладки
        for idx, layout_data in enumerate(layouts_data):
            row = idx // cols
            col = idx % cols
            ax = axes[row, col] if rows > 1 and cols > 1 else axes[idx]

            word_stats = layout_data.get("word_stats")
            if not word_stats:
                ax.set_visible(False)
                continue

            # Данные для диаграммы
            loads = [word_stats["left_only"], word_stats["right_only"], word_stats["both"]]
            labels = ['Только левая рука', 'Только правая рука', 'Обе руки']
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

            # Рисуем круговую диаграмму
            ax.pie(loads, labels=labels, autopct='%1.1f%%',
                   colors=colors, startangle=90, counterclock=False)
            alias = self._normalize_name(layout_data["name"])
            label = self.layout_labels.get(alias, layout_data["name"])
            ax.set_title(f'{label}\n(Общая нагрузка: {layout_data["total"]})',
                         fontsize=12, fontweight='bold')

        # Прячем пустые диаграммы
        for idx in range(len(layouts_data), rows * cols):
            row = idx // cols
            col = idx % cols
            if rows > 1 and cols > 1:
                axes[row, col].set_visible(False)
            else:
                axes[idx].set_visible(False)

        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        plt.show()

    def showAll(self, results: list, corpus_name: str = "text"):
        """
        ПОКАЗЫВАЕТ ВСЕ ГРАФИКИ для одного набора данных.
        Как главная кнопка "показать все диаграммы".
        """
        # Подготавливаем данные
        structured, all_layouts_data = self._prepare_results(results)

        # Рисуем основные графики
        self._create_all_layouts_comparison_chart(all_layouts_data, corpus_name)
        self._create_total_load_chart(all_layouts_data, corpus_name)
        self._create_hand_distribution_chart(all_layouts_data, corpus_name)

        # Круговые диаграммы только для обычного текста
        if corpus_name == "text":
            self._create_hand_pie_charts(structured, corpus_name)

        return structured

    def showAllFromDict(self, results_dict: dict):
        """
        ПОКАЗЫВАЕТ ГРАФИКИ ДЛЯ ВСЕХ ТИПОВ ДАННЫХ.
        Работает с результатами анализа текста, биграмм, 1-грамм и CSV.
        """
        # Проходим по всем типам данных и рисуем графики
        for corpus_name, results in results_dict.items():
            print(f"\n=== Построение графиков для корпуса: {corpus_name} ===")
            self.showAll(results, corpus_name=corpus_name)
