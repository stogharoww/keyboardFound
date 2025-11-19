import matplotlib.pyplot as plt
import numpy as np


class GraphicsAnalyzer:
    def __init__(self, layouts: dict):
        self.layouts = layouts

        # Цвета для раскладок
        self.layout_colors = {
            "qwerty": "red",
            "yaverty": "purple",
            "vizov": "black"
        }

        # Русские названия для легенды
        self.layout_labels = {
            "qwerty": "йцукен",
            "vizov": "вызов",
            "yaverty": "яверты"
        }

        # Подписи пальцев
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

        self.finger_order = ['lfi5', 'lfi4', 'lfi3', 'lfi2', 'lfi1',
                             'rfi1', 'rfi2', 'rfi3', 'rfi4', 'rfi5']

    def _normalize_name(self, name: str) -> str:
        clean = name.strip().lower().replace("\n", "").replace("\r", "")
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
        structured = []
        all_layouts_data = []

        for res in results:
            if isinstance(res, dict):
                layout_name = res["layout_name"]
                total_load = res["total_load"]
                hand_switches = res["hand_switches"]
                modifier_count = res["modifier_count"]
                finger_stats = res["finger_statistics"]
                word_stats = res.get("word_stats")
            else:
                if len(res) == 6:
                    layout_name, total_load, hand_switches, modifier_count, finger_stats, word_stats = res
                else:
                    layout_name, total_load, hand_switches, modifier_count, finger_stats = res
                    word_stats = None

            all_fingers = set(self.layouts[layout_name]["fingerKey"].keys())
            for f in all_fingers:
                if f not in finger_stats:
                    finger_stats[f] = 0

            structured.append({
                "layout_name": layout_name,
                "total_load": total_load,
                "hand_switches": hand_switches,
                "modifier_count": modifier_count,
                "finger_statistics": finger_stats,
                "word_stats": word_stats
            })

            all_layouts_data.append({
                "name": layout_name,
                "stats": finger_stats,
                "total": total_load,
                "hand_switches": hand_switches,
                "modifier_count": modifier_count,
                "word_stats": word_stats
            })

        return structured, all_layouts_data

    # ---------------- Графики ----------------

    def _create_all_layouts_comparison_chart(self, layouts_data: list, corpus_name: str):
        """Единый график сравнения нагрузки по пальцам для всех раскладок."""
        if not layouts_data:
            return

        fingers = [self.finger_names_ru.get(f, f) for f in self.finger_order]
        y_pos = np.arange(len(fingers))
        bar_height = 0.2
        fig, ax = plt.subplots(figsize=(14, 6))

        for i, layout_data in enumerate(layouts_data):
            alias = self._normalize_name(layout_data["name"])
            layout_color = self.layout_colors.get(alias, 'gray')
            label = self.layout_labels.get(alias, layout_data["name"])
            values = [layout_data["stats"].get(f, 0) for f in self.finger_order]

            offset = (i - (len(layouts_data) - 1) / 2) * bar_height
            bars = ax.barh(y_pos + offset, values, height=bar_height,
                           color=layout_color, alpha=0.7, label=label)

            total = sum(values)
            max_val = max(values) if values else 1
            for bar, value in zip(bars, values):
                percent = value / total * 100 if total else 0
                width = bar.get_width()
                ax.text(width + max_val * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f'{percent:.1f}%',
                        ha='left', va='center', fontsize=8)

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
        names = [layout["name"] for layout in layouts_data]
        totals = [layout["total"] for layout in layouts_data]

        fig, ax = plt.subplots(figsize=(14, 2.5))
        y_pos = np.arange(len(names))

        colors = [self.layout_colors.get(self._normalize_name(name), 'gray') for name in names]
        labels = [self.layout_labels.get(self._normalize_name(name), name) for name in names]
        bars = ax.barh(y_pos, totals, color=colors, alpha=0.7)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=11)
        ax.set_xlabel('Общая нагрузка (единицы пути)', fontsize=12)
        ax.set_title(f'Общая нагрузка по раскладкам ({corpus_name})',
                     fontsize=14, fontweight='bold')

        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()

    def _create_hand_distribution_chart(self, layouts_data: list, corpus_name: str):
        names = [layout["name"] for layout in layouts_data]
        left_loads, right_loads = [], []

        for layout in layouts_data:
            left_load = sum(v for k, v in layout["stats"].items() if k.startswith('l'))
            right_load = sum(v for k, v in layout["stats"].items() if k.startswith('r'))
            left_loads.append(left_load)
            right_loads.append(right_load)

        y = np.arange(len(names))
        height = 0.35

        fig, ax = plt.subplots(figsize=(14, 2.5))

        colors = [self.layout_colors.get(self._normalize_name(name), 'gray') for name in names]
        labels = [self.layout_labels.get(self._normalize_name(name), name) for name in names]

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
        """Круговые диаграммы: слова только левой рукой, только правой рукой, обе руки."""
        n_layouts = len(layouts_data)
        if n_layouts == 0:
            return

        cols = min(2, n_layouts)
        rows = (n_layouts + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
        fig.suptitle(f'Круговые диаграммы распределения слов по рукам ({corpus_name})',
                     fontsize=16, fontweight='bold')

        if n_layouts == 1:
            axes = np.array([axes])
        if rows == 1 and cols == 1:
            axes = np.array([axes])
        elif rows == 1:
            axes = axes.reshape(1, -1)
        elif cols == 1:
            axes = axes.reshape(-1, 1)

        for idx, layout_data in enumerate(layouts_data):
            row = idx // cols
            col = idx % cols
            ax = axes[row, col] if rows > 1 and cols > 1 else axes[idx]

            word_stats = layout_data.get("word_stats")
            if not word_stats:
                ax.set_visible(False)
                continue

            loads = [word_stats["left_only"], word_stats["right_only"], word_stats["both"]]
            labels = ['Только левая рука', 'Только правая рука', 'Обе руки']
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

            ax.pie(loads, labels=labels, autopct='%1.1f%%',
                   colors=colors, startangle=90, counterclock=False)
            alias = self._normalize_name(layout_data["name"])
            label = self.layout_labels.get(alias, layout_data["name"])
            ax.set_title(f'{label}\n(Общая нагрузка: {layout_data["total"]})',
                         fontsize=12, fontweight='bold')

        # Скрываем пустые оси
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
        Построение всех графиков и диаграмм для одного корпуса.
        Если corpus_name == 'text', дополнительно строятся круговые диаграммы.
        """
        structured, all_layouts_data = self._prepare_results(results)

        # Основные графики
        self._create_all_layouts_comparison_chart(all_layouts_data, corpus_name)
        self._create_total_load_chart(all_layouts_data, corpus_name)
        self._create_hand_distribution_chart(all_layouts_data, corpus_name)

        # Круговые диаграммы только для корпуса 'text'
        if corpus_name == "text":
            self._create_hand_pie_charts(structured, corpus_name)

        return structured

    def showAllFromDict(self, results_dict: dict):
        """
        Построение графиков для всех корпусов по очереди.
        results_dict: словарь вида {"text": [...], "digramms": [...], "onegramms": [...], "csv": [...]}
        """
        for corpus_name, results in results_dict.items():
            print(f"\n=== Построение графиков для корпуса: {corpus_name} ===")
            self.showAll(results, corpus_name=corpus_name)
