import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


class GraphicsAnalyzer:
    def __init__(self, layouts: dict):
        self.layouts = layouts

        # Русские названия пальцев для подписей
        self.finger_names_ru = {
            'lfi5': 'Левый мизинец',
            'lfi4': 'Левый безымянный',
            'lfi3': 'Левый средний',
            'lfi2': 'Левый указательный',
            'lfi1': 'Левый большой',
            'rfi2': 'Правый указательный',
            'rfi3': 'Правый средний',
            'rfi4': 'Правый безымянный',
            'rfi5': 'Правый мизинец'
        }

        # Порядок пальцев для отображения (слева направо)
        self.finger_order = ['lfi5', 'lfi4', 'lfi3', 'lfi2', 'lfi1',
                             'rfi2', 'rfi3', 'rfi4', 'rfi5']

    def returnResults(self, results: list) -> list:
        """Формирует результаты в структурированном виде и выводит графики нагрузки на пальцы"""
        structured = []
        all_layouts_data = []

        for res in results:
            layout_name, total_load, hand_switches, modifier_count, finger_stats = res

            # Добавляем нули для всех пальцев, чтобы они всегда были в выводе
            all_fingers = set(self.layouts[layout_name]["fingerKey"].keys())
            for f in all_fingers:
                if f not in finger_stats:
                    finger_stats[f] = 0

            # Убираем None, чтобы не ломать графики
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

        # Создаем сравнительные графики
        self._create_comparison_charts(all_layouts_data)

        return structured

    def _create_comparison_charts(self, layouts_data: list):
        """Создает несколько типов графиков для сравнения раскладок"""

        # 1. Общий сравнительный график всех раскладок
        self._create_combined_comparison_chart(layouts_data)

        # 2. Отдельные графики для каждой раскладки
        self._create_individual_charts(layouts_data)

        # 3. График общей нагрузки по раскладкам
        self._create_total_load_chart(layouts_data)

        # 4. График распределения нагрузки по рукам
        self._create_hand_distribution_chart(layouts_data)

    def _create_combined_comparison_chart(self, layouts_data: list):
        """Создает один большой график со всеми раскладками для сравнения"""

        n_layouts = len(layouts_data)
        if n_layouts == 0:
            return

        # Создаем subplot с несколькими колонками
        cols = min(2, n_layouts)  # Максимум 2 колонки
        rows = (n_layouts + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(16, 6 * rows))
        fig.suptitle('Сравнение нагрузки по пальцам для разных раскладок',
                     fontsize=16, fontweight='bold')

        # Если одна раскладка, делаем axes массивом для единообразия
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

        # Скрываем пустые subplots
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
        """Создает отдельные графики для каждой раскладки"""

        for layout_data in layouts_data:
            fig, ax = plt.subplots(figsize=(12, 6))
            self._plot_single_layout(ax, layout_data)
            plt.tight_layout()
            plt.show()

    def _plot_single_layout(self, ax, layout_data: dict):
        """Отрисовывает один график для конкретной раскладки"""

        layout_name = layout_data["name"]
        finger_stats = layout_data["stats"]

        # Подготавливаем данные в правильном порядке
        fingers = []
        values = []
        colors = []

        for finger in self.finger_order:
            if finger in finger_stats:
                fingers.append(self.finger_names_ru.get(finger, finger))
                values.append(finger_stats[finger])
                # Разные цвета для левой и правой руки
                if finger.startswith('l'):
                    colors.append('#1f77b4')  # Синий для левой руки
                else:
                    colors.append('#ff7f0e')  # Оранжевый для правой руки

        # Горизонтальный бар-чарт
        y_pos = np.arange(len(fingers))
        bars = ax.barh(y_pos, values, color=colors, alpha=0.7)

        # Настройки осей
        ax.set_yticks(y_pos)
        ax.set_yticklabels(fingers, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel('Нагрузка', fontsize=12)
        ax.set_title(f'{layout_name}\n(Общая нагрузка: {layout_data["total"]})',
                     fontsize=13, fontweight='bold')

        # Добавляем значения на бары
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.text(width + max(values) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f'{int(value)}', ha='left', va='center', fontsize=9)

        # Настройка сетки
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        # Легенда для рук
        legend_elements = [
            Patch(facecolor='#1f77b4', alpha=0.7, label='Левая рука'),
            Patch(facecolor='#ff7f0e', alpha=0.7, label='Правая рука')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        # Автоматическая настройка пределов по x
        max_val = max(values) if values else 1
        ax.set_xlim(0, max_val * 1.15)

    def _create_total_load_chart(self, layouts_data: list):
        """Создает график общей нагрузки по раскладкам"""

        names = [layout["name"] for layout in layouts_data]
        totals = [layout["total"] for layout in layouts_data]

        fig, ax = plt.subplots(figsize=(12, 6))

        bars = ax.bar(names, totals,
                      color=['#2ecc71', '#e74c3c', '#3498db', '#f39c12'][:len(names)],
                      alpha=0.7)

        ax.set_title('Общая нагрузка по раскладкам', fontsize=14, fontweight='bold')
        ax.set_ylabel('Общая нагрузка', fontsize=12)

        # Добавляем значения на бары
        for bar, value in zip(bars, totals):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + max(totals) * 0.01,
                    f'{int(value)}', ha='center', va='bottom', fontsize=11)

        plt.xticks(rotation=45)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.show()

    def _create_hand_distribution_chart(self, layouts_data: list):
        """Создает график распределения нагрузки между руками"""

        names = [layout["name"] for layout in layouts_data]
        left_loads = []
        right_loads = []

        for layout in layouts_data:
            # Суммируем нагрузку по пальцам левой и правой руки
            left_load = sum(v for k, v in layout["stats"].items() if k.startswith('l'))
            right_load = sum(v for k, v in layout["stats"].items() if k.startswith('r'))
            left_loads.append(left_load)
            right_loads.append(right_load)

        x = np.arange(len(names))
        width = 0.35

        fig, ax = plt.subplots(figsize=(12, 6))

        bars1 = ax.bar(x - width / 2, left_loads, width,
                       label='Левая рука', color='#1f77b4', alpha=0.7)
        bars2 = ax.bar(x + width / 2, right_loads, width,
                       label='Правая рука', color='#ff7f0e', alpha=0.7)

        ax.set_title('Распределение нагрузки между руками',
                     fontsize=14, fontweight='bold')
        ax.set_ylabel('Нагрузка', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45)
        ax.legend()

        # Добавляем значения на бары
        max_val = max(left_loads + right_loads) if (left_loads + right_loads) else 1
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2.,
                        height + max_val * 0.01,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=9)

        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.show()
    def renderAll(self, results: list) -> list:
        """
        Полный цикл: принимает результаты анализа (из TextAnalyzer.compareLayouts),
        структурирует их и строит все графики:
          1. Сравнение нагрузки по пальцам для всех раскладок
          2. Отдельные графики для каждой раскладки
          3. Общая нагрузка по раскладкам
          4. Распределение нагрузки между руками

        :param results: список результатов вида
                        [layout_name, total_load, hand_switches, modifier_count, finger_stats]
        :return: structured — список словарей с данными по каждой раскладке
        """
        structured = []
        all_layouts_data = []

        for res in results:
            layout_name, total_load, hand_switches, modifier_count, finger_stats = res

            # Добавляем нули для всех пальцев, чтобы они всегда были в выводе
            all_fingers = set(self.layouts[layout_name]["fingerKey"].keys())
            for f in all_fingers:
                if f not in finger_stats:
                    finger_stats[f] = 0

            # Убираем None, чтобы не ломать графики
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

        # Строим все графики
        self._create_comparison_charts(all_layouts_data)

        return structured
