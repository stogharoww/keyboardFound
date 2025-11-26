try:
    import matplotlib.pyplot as plt
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
    NUMPY_AVAILABLE = True
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    MATPLOTLIB_AVAILABLE = False
    NUMPY_AVAILABLE = False

import random


def get_layout_colors() -> dict:
    """
    Фиксированные цвета для раскладок в заданном порядке:
    йцукен → красный, вызов → тёмно-синий, диктор → фиолетовый,
    яверты → чёрный, ант → жёлтый, зубачев → голубой, скоропись → розовый
    """
    layouts = ["йцукен", "вызов", "диктор", "яверты", "ант", "зубачев", "скоропись"]
    hex_colors = ["#FF0000", "#000000", "#FFFF00", "#FF1493", "#0000FF", "#800080", "#00FF00"]

    return {name: color for name, color in zip(layouts, hex_colors)}


class GraphicsAnalyzer:
    def __init__(self, layouts: dict):
        self.layouts = layouts
        self.layout_colors = get_layout_colors()
        self.layout_labels = {
            "йцукен": "йцукен", "вызов": "вызов", "яверты": "яверты",
            "ант": "ант", "скоропись": "скоропись", "зубачев": "зубачёв", "диктор": "диктор",
        }

        self.finger_names_ru = {
            'lfi5': 'Левый мизинец', 'lfi4': 'Левый безымянный', 'lfi3': 'Левый средний',
            'lfi2': 'Левый указательный', 'lfi1': 'Левый большой', 'rfi1': 'Правый большой',
            'rfi2': 'Правый указательный', 'rfi3': 'Правый средний', 'rfi4': 'Правый безымянный',
            'rfi5': 'Правый мизинец'
        }

        self.finger_order = ['lfi5', 'lfi4', 'lfi3', 'lfi2', 'lfi1', 'rfi1', 'rfi2', 'rfi3', 'rfi4', 'rfi5']

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
                elif len(res) == 5:
                    layout_name, total_load, hand_switches, modifier_count, finger_stats = res
                    word_stats = None
                else:
                    raise ValueError(f"Неподдерживаемый формат результата: {res}")

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

    def _create_all_layouts_comparison_chart(self, layouts_data: list, corpus_name: str):
        if not layouts_data or not NUMPY_AVAILABLE:
            return

        fingers = [self.finger_names_ru.get(f, f) for f in self.finger_order]
        spacing = 1.5
        y_pos = np.arange(len(fingers)) * spacing

        n_layouts = len(layouts_data)
        bar_height = min(1.4 / max(n_layouts, 1), 0.4)
        fig_height = max(7, len(fingers) * 0.8)

        fig, ax = plt.subplots(figsize=(14, fig_height))

        for i, layout_data in enumerate(layouts_data):
            name = layout_data["name"]
            layout_color = self.layout_colors.get(name, f"#{random.randint(0x100000, 0xFFFFFF):06x}")
            label = self.layout_labels.get(name, name)
            values = [layout_data["stats"].get(f, 0) for f in self.finger_order]

            offset = (i - (n_layouts - 1) / 2) * bar_height
            bars = ax.barh(y_pos + offset, values, height=bar_height,
                           color=layout_color, alpha=0.85, label=label)

            total = sum(values)
            max_val = max(values) if values else 1
            for bar, value in zip(bars, values):
                if value == 0 or total == 0:
                    continue
                percent = value / total * 100
                width = bar.get_width()
                ax.text(width + max_val * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f'{percent:.1f}%',
                        ha='left', va='center', fontsize=9)

        for y in y_pos:
            ax.axhline(y=y, color='gray', linestyle='--', linewidth=0.5, alpha=0.4)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(fingers, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel('Нагрузка (единицы пути)', fontsize=13)
        ax.set_title(f'Сравнение нагрузки по пальцам ({corpus_name})',
                     fontsize=15, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        plt.tight_layout()
        plt.show()

    def _create_total_load_chart(self, layouts_data: list, corpus_name: str):
        names = [layout["name"] for layout in layouts_data]
        totals = [layout["total"] for layout in layouts_data]

        # Вычисляем общую сумму нагрузки всех раскладок
        total_sum = sum(totals) if totals else 1
        # Вычисляем проценты от общей суммы (как в других графиках)
        percentages = [(total / total_sum * 100) for total in totals]

        fig, ax = plt.subplots(figsize=(14, 2.8))
        y_pos = np.arange(len(names))

        colors = [self.layout_colors.get(name, 'gray') for name in names]
        labels = [self.layout_labels.get(name, name) for name in names]
        bars = ax.barh(y_pos, percentages, color=colors, alpha=0.8)

        # Подписи справа с процентами (как в других графиках)
        for i, (percent, total) in enumerate(zip(percentages, totals)):
            ax.text(percent * 1.01, i, f'{percent:.1f}%', va='center', ha='left', fontsize=10, color='#333')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=11)
        ax.set_xlabel('Доля нагрузки (%)', fontsize=12)
        ax.set_title(f'Общая нагрузка по раскладкам ({corpus_name})',
                     fontsize=14, fontweight='bold')

        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()

    def _create_hand_distribution_chart(self, layouts_data: list, corpus_name: str):
        if not layouts_data or not NUMPY_AVAILABLE:
            return

        names = [layout["name"] for layout in layouts_data]
        left_loads, right_loads = [], []

        for layout in layouts_data:
            left_load = sum(v for k, v in layout["stats"].items() if k.startswith('l'))
            right_load = sum(v for k, v in layout["stats"].items() if k.startswith('r'))
            left_loads.append(left_load)
            right_loads.append(right_load)

        y = np.arange(len(names))  # Теперь np.arange должен работать
        height = 0.35

        fig, ax = plt.subplots(figsize=(14, 2.8))

        colors = [self.layout_colors.get(name, 'gray') for name in names]
        labels = [self.layout_labels.get(name, name) for name in names]

        ax.barh(y - height / 2, left_loads, height,
                label='Левая рука', color=colors, alpha=0.75)
        ax.barh(y + height / 2, right_loads, height,
                label='Правая рука', color=colors, alpha=0.45)

        for i, (l, r) in enumerate(zip(left_loads, right_loads)):
            total = l + r
            if total > 0:
                ax.text(max(l, r) * 1.01, i - height / 2, f'{(l / total * 100):.1f}%', va='center', fontsize=9)
                ax.text(max(l, r) * 1.01, i + height / 2, f'{(r / total * 100):.1f}%', va='center', fontsize=9)

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
        if not layouts_data or not MATPLOTLIB_AVAILABLE:
            return

        n_layouts = len(layouts_data)
        if n_layouts == 0:
            return

        cols = 3
        rows = (n_layouts + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
        fig.suptitle(f'Круговые диаграммы распределения слов по рукам ({corpus_name})',
                     fontsize=16, fontweight='bold')

        axes = axes.flatten() if n_layouts > 1 else [axes]

        for idx, layout_data in enumerate(layouts_data):
            ax = axes[idx]
            word_stats = layout_data.get("word_stats")
            if not word_stats:
                ax.set_visible(False)
                continue

            loads = [word_stats.get("left_only", 0),
                     word_stats.get("right_only", 0),
                     word_stats.get("both", 0)]
            labels = []
            values = []
            colors = []
            if loads[0] > 0:
                labels.append('Только левая рука')
                values.append(loads[0])
                colors.append('#1f77b4')
            if loads[1] > 0:
                labels.append('Только правая рука')
                values.append(loads[1])
                colors.append('#ff7f0e')
            if loads[2] > 0:
                labels.append('Обе руки')
                values.append(loads[2])
                colors.append('#2ca02c')

            if not values:
                ax.set_visible(False)
                continue

            ax.pie(values, labels=labels, autopct='%1.1f%%',
                   colors=colors, startangle=90, counterclock=False)
            name = layout_data["name"]
            label = self.layout_labels.get(name, name)
            ax.set_title(f'{label}\n(Общая нагрузка: {layout_data["total"]:.0f})',
                         fontsize=12, fontweight='bold')

        for idx in range(n_layouts, len(axes)):
            axes[idx].set_visible(False)

        plt.tight_layout()
        plt.subplots_adjust(top=0.88, hspace=0.4)
        plt.show()

    def showAll(self, results: list, corpus_name: str = "text"):
        structured, all_layouts_data = self._prepare_results(results)

        if MATPLOTLIB_AVAILABLE and NUMPY_AVAILABLE:
            self._create_all_layouts_comparison_chart(all_layouts_data, corpus_name)
            self._create_total_load_chart(all_layouts_data, corpus_name)
            self._create_hand_distribution_chart(all_layouts_data, corpus_name)

            if corpus_name == "text":
                self._create_hand_pie_charts(structured, corpus_name)
        else:
            print("Для отображения графиков установите numpy и matplotlib: pip install numpy matplotlib")

        return structured

    def showAllFromDict(self, results_dict: dict):
        for corpus_name, results in results_dict.items():
            print(f"\n=== Построение графиков для текста: {corpus_name} ===")
            self.showAll(results, corpus_name=corpus_name)

    def showAveragedAll(self, results_dict: dict, corpus_name: str = "Среднее по текстам"):
        layout_accumulator = {}

        for corpus_results in results_dict.values():
            for res in corpus_results:
                if len(res) == 6:
                    layout_name, total, hand_switches, modifier_count, finger_stats, word_stats = res
                elif len(res) == 5:
                    layout_name, total, hand_switches, modifier_count, finger_stats = res
                    word_stats = None
                else:
                    raise ValueError(f"Неподдерживаемый формат результата: {res}")

                if layout_name not in layout_accumulator:
                    layout_accumulator[layout_name] = {
                        "finger_stats": [],
                        "total": [],
                        "hand_switches": [],
                        "modifier_count": [],
                        "word_stats": []
                    }

                layout_accumulator[layout_name]["finger_stats"].append(finger_stats)
                layout_accumulator[layout_name]["total"].append(total)
                layout_accumulator[layout_name]["hand_switches"].append(hand_switches)
                layout_accumulator[layout_name]["modifier_count"].append(modifier_count)
                if word_stats:
                    layout_accumulator[layout_name]["word_stats"].append(word_stats)

        averaged_layouts = []
        for layout_name, data in layout_accumulator.items():
            n = len(data["finger_stats"])
            finger_sums = {f: 0 for f in self.finger_order}
            for stats in data["finger_stats"]:
                for f in self.finger_order:
                    finger_sums[f] += stats.get(f, 0)
            averaged_stats = {f: finger_sums[f] / n if n else 0 for f in self.finger_order}

            total_avg = sum(data["total"]) / n if n else 0
            hand_switches_avg = sum(data["hand_switches"]) / n if n else 0
            modifier_count_avg = sum(data["modifier_count"]) / n if n else 0

            word_stats_avg = None
            if data["word_stats"]:
                word_keys = ["left_only", "right_only", "both"]
                word_sums = {k: 0 for k in word_keys}
                for ws in data["word_stats"]:
                    for k in word_keys:
                        word_sums[k] += ws.get(k, 0)
                denom = len(data["word_stats"])
                word_stats_avg = {k: (word_sums[k] / denom if denom else 0) for k in word_keys}

            averaged_layouts.append({
                "name": layout_name,
                "stats": averaged_stats,
                "total": total_avg,
                "hand_switches": hand_switches_avg,
                "modifier_count": modifier_count_avg,
                "word_stats": word_stats_avg
            })

        self._create_all_layouts_comparison_chart(averaged_layouts, corpus_name)
        self._create_total_load_chart(averaged_layouts, corpus_name)
        self._create_hand_distribution_chart(averaged_layouts, corpus_name)
        self._create_hand_pie_charts(averaged_layouts, corpus_name)
