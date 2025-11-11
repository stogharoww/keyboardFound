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
            "vizov": "vizov"
        }
        return mapping.get(clean, clean)

    def _prepare_results(self, results: list) -> tuple[list, list]:
        structured = []
        all_layouts_data = []

        for res in results:
            layout_name, total_load, hand_switches, modifier_count, finger_stats = res

            all_fingers = set(self.layouts[layout_name]["fingerKey"].keys())
            for f in all_fingers:
                if f not in finger_stats:
                    finger_stats[f] = 0

            finger_stats = {k: v for k, v in finger_stats.items() if k is not None}

            structured.append({
                "layout_name": layout_name,
                "total_load": total_load,
                "hand_switches": hand_switches,
                "modifier_count": modifier_count,
                "finger_statistics": finger_stats
            })

            all_layouts_data.append({
                "name": layout_name,
                "stats": finger_stats,
                "total": total_load,
                "hand_switches": hand_switches,
                "modifier_count": modifier_count
            })

        return structured, all_layouts_data

    def returnResults(self, results: list) -> list:
        structured, all_layouts_data = self._prepare_results(results)
        self._create_comparison_charts(all_layouts_data)
        return structured

    def renderAll(self, results: list) -> list:
        structured, all_layouts_data = self._prepare_results(results)
        self._create_comparison_charts(all_layouts_data)
        return structured

    # ---------------- Графики ----------------

    def _create_comparison_charts(self, layouts_data: list):
        self._create_combined_comparison_chart(layouts_data)
        self._create_individual_charts(layouts_data)
        self._create_total_load_chart(layouts_data)
        self._create_hand_distribution_chart(layouts_data)
        self._create_hand_pie_charts(layouts_data)

    def _create_combined_comparison_chart(self, layouts_data: list):
        n_layouts = len(layouts_data)
        if n_layouts == 0:
            return

        cols = min(2, n_layouts)
        rows = (n_layouts + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(16, 6 * rows))
        fig.suptitle('Сравнение нагрузки по пальцам для разных раскладок',
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
            self._plot_single_layout(ax, layout_data)

        for idx in range(len(layouts_data), rows * cols):
            row = idx // cols
            col = idx % cols
            if rows > 1 and cols > 1:
                axes[row, col].set_visible(False)
            else:
                axes[idx].set_visible(False)

        plt.tight_layout()
        plt.subplots_adjust(top=0.94)
        plt.show()

    def _create_individual_charts(self, layouts_data: list):
        for layout_data in layouts_data:
            fig, ax = plt.subplots(figsize=(12, 6))
            self._plot_single_layout(ax, layout_data)
            plt.tight_layout()
            plt.show()

    def _plot_single_layout(self, ax, layout_data: dict):
        layout_name = layout_data["name"]
        finger_stats = layout_data["stats"]

        fingers, values, colors = [], [], []

        alias = self._normalize_name(layout_name)
        layout_color = self.layout_colors.get(alias, 'gray')

        for finger in self.finger_order:
            if finger in finger_stats:
                fingers.append(self.finger_names_ru.get(finger, finger))
                values.append(finger_stats[finger])
                colors.append(layout_color)

        y_pos = np.arange(len(fingers))
        bars = ax.barh(y_pos, values, color=colors, alpha=0.7)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(fingers, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel('Нагрузка', fontsize=12)
        ax.set_title(f'{layout_name}\n(Общая нагрузка: {layout_data["total"]})',
                     fontsize=13, fontweight='bold')

        if values:
            max_val = max(values)
            for bar, value in zip(bars, values):
                width = bar.get_width()
                ax.text(width + max_val * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f'{int(value)}', ha='left', va='center', fontsize=9)

        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        ax.set_xlim(0, max(values) * 1.15 if values else 1)

    def _create_total_load_chart(self, layouts_data: list):
        names = [layout["name"] for layout in layouts_data]
        totals = [layout["total"] for layout in layouts_data]

        fig, ax = plt.subplots(figsize=(12, 6))
        y_pos = np.arange(len(names))

        colors = [self.layout_colors.get(self._normalize_name(name), 'gray') for name in names]
        bars = ax.barh(y_pos, totals, color=colors, alpha=0.7)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=11)
        ax.set_xlabel('Общая нагрузка', fontsize=12)
        ax.set_title('Общая нагрузка по раскладкам', fontsize=14, fontweight='bold')

        max_total = max(totals) if totals else 1
        for bar, value in zip(bars, totals):
            width = bar.get_width()
            ax.text(width + max_total * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f'{int(value)}', ha='left', va='center', fontsize=11)

        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()

    def _create_hand_distribution_chart(self, layouts_data: list):
        names = [layout["name"] for layout in layouts_data]
        left_loads, right_loads = [], []

        for layout in layouts_data:
            left_load = sum(v for k, v in layout["stats"].items() if k.startswith('l'))
            right_load = sum(v for k, v in layout["stats"].items() if k.startswith('r'))
            left_loads.append(left_load)
            right_loads.append(right_load)

        y = np.arange(len(names))
        height = 0.35

        fig, ax = plt.subplots(figsize=(12, 6))

        colors = [self.layout_colors.get(self._normalize_name(name), 'gray') for name in names]

        bars1 = ax.barh(y - height / 2, left_loads, height,
                        label='Левая рука', color=colors, alpha=0.7)
        bars2 = ax.barh(y + height / 2, right_loads, height,
                        label='Правая рука', color=colors, alpha=0.4)

        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=11)
        ax.set_xlabel('Нагрузка', fontsize=12)
        ax.set_title('Распределение нагрузки между руками', fontsize=14, fontweight='bold')
        ax.legend()

        max_val = max(left_loads + right_loads) if (left_loads + right_loads) else 1
        for bars in (bars1, bars2):
            for bar in bars:
                width = bar.get_width()
                ax.text(width + max_val * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f'{int(width)}',
                        ha='left', va='center', fontsize=9)

        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()

    def _create_hand_pie_charts(self, layouts_data: list):
        """Создает круговые диаграммы распределения нагрузки между руками для каждой раскладки"""
        n_layouts = len(layouts_data)
        if n_layouts == 0:
            return

        cols = min(2, n_layouts)  # максимум 2 диаграммы в строке
        rows = (n_layouts + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
        fig.suptitle('Круговые диаграммы распределения нагрузки между руками',
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

            left_load = sum(v for k, v in layout_data["stats"].items() if k.startswith('l'))
            right_load = sum(v for k, v in layout_data["stats"].items() if k.startswith('r'))

            loads = [left_load, right_load]
            labels = ['Левая рука', 'Правая рука']
            colors = ['#1f77b4', '#ff7f0e']

            ax.pie(loads, labels=labels, autopct='%1.1f%%',
                   colors=colors, startangle=90, counterclock=False)
            ax.set_title(f'{layout_data["name"]}\n(Общая нагрузка: {layout_data["total"]})',
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

