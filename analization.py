"""
Оптимизированный модуль для анализа эргономики раскладок клавиатуры.
Считает нагрузку по длине пути пальцев, модификаторам и смене рук.
Анализирует текст, биграммы и CSV-файл с частотами.
"""

import asyncio
import unicodedata
import threading
import pandas as pd
from keyboardInit import keyInitializations
from tqdm import tqdm
from typing import Dict, Tuple, Optional


class TextAnalyzer:
    """
    Основной класс для анализа эргономики раскладок клавиатуры.

    Атрибуты:
        shtraf_config (dict): Конфигурация штрафов за различные действия
        debug_mode (bool): Режим отладки
        layouts (dict): Загруженные раскладки клавиатуры
        index_shtraf (Dict[str, int]): Карта индексов к штрафам
        sym_best (Dict[str, Dict[str, Tuple[str, dict]]]): Лучшие варианты символов
        idx_to_finger (Dict[str, Dict[str, str]]): Соответствие индексов пальцам
        explicit_shift_syms (Dict[str, set]): Символы с явным шифтом
        lookup_maps (Dict[str, Dict[str, Tuple[str, dict, str]]]): Быстрые карты поиска
        last_results (dict): Последние результаты анализа
    """

    def __init__(self,
                 shtraf_config: dict | None = None,
                 debug_mode: bool = False):
        """
        Инициализация анализатора текста.

        Args:
            shtraf_config (dict | None): Конфигурация штрафов. Если None, используется стандартная
            debug_mode (bool): Включить режим отладки
        """
        self.shtraf_config = shtraf_config or {
            'shift_penalty':          2,
            'alt_penalty':            3,
            'ctrl_penalty':           4,
            'same_finger_penalty':    1,
            'hand_switch_penalty':    1
        }
        self.debug_mode = debug_mode
        self.layouts: dict[str, dict] = {}

        # Вспомогательные карты
        self.index_shtraf: Dict[str, int] = {}
        self.sym_best: Dict[str, Dict[str, Tuple[str, dict]]] = {}
        self.idx_to_finger: Dict[str, Dict[str, str]] = {}
        self.explicit_shift_syms: Dict[str, set] = {}
        self.lookup_maps: Dict[str, Dict[str, Tuple[str, dict, str]]] = {}

        # Последние результаты анализа
        self.last_results: dict = {}

    async def keybsInits(self):
        """
        Загрузка раскладок клавиатуры и построение вспомогательных карт.

        Инициализирует:
            - layouts: словарь всех раскладок
            - index_shtraf: карта штрафов по индексам
            - sym_best: лучшие варианты для символов
            - idx_to_finger: соответствие индексов пальцам
            - explicit_shift_syms: символы с явным шифтом
            - lookup_maps: быстрые карты для поиска символов

        Returns:
            None
        """
        self.layouts = await keyInitializations()

        # Построить index_shtraf
        shtraf_layout = self.layouts.get("ШТРАФЫ", {})
        shtraf_bukvaKey = shtraf_layout.get("bukvaKey", {})
        self.index_shtraf.clear()
        for idx, vals in shtraf_bukvaKey.items():
            if not vals:
                continue
            try:
                self.index_shtraf[idx] = int(vals[0])
            except (ValueError, TypeError):
                continue

        # Для каждой раскладки подготовить карты
        for name, lay in self.layouts.items():
            if name == "ШТРАФЫ":
                continue

            bukvaKey = lay.get("bukvaKey", {})
            modifierMap = lay.get("modifierMap", {})
            fingerKey = lay.get("fingerKey", {})

            # idx → finger
            idx_to_finger_map: Dict[str, str] = {}
            for finger, idxs in fingerKey.items():
                for idx in idxs:
                    idx_to_finger_map[idx] = finger
            self.idx_to_finger[name] = idx_to_finger_map

            # sym → лучший вариант (idx, mod_info)
            best_map: Dict[str, Tuple[str, dict]] = {}
            explicit_shift_set = set()
            for idx, syms in bukvaKey.items():
                for s in syms:
                    info = modifierMap.get(s, {})
                    if info.get('shift', False):
                        explicit_shift_set.add(s)
                    base = self.index_shtraf.get(idx, 10**6)
                    if s not in best_map or base < self.index_shtraf.get(best_map[s][0], 10**6):
                        best_map[s] = (idx, info)
            self.sym_best[name] = best_map
            self.explicit_shift_syms[name] = explicit_shift_set

            # Быстрый lookup: символ → (idx, mod_info, finger)
            lookup = {}
            for s, (idx, info) in best_map.items():
                lookup[s] = (idx, info, idx_to_finger_map.get(idx))
                lookup[s.lower()] = (idx, info, idx_to_finger_map.get(idx))
            self.lookup_maps[name] = lookup

    def base_index_shtraf(self, idx: str) -> int:
        """
        Получить базовый штраф для индекса клавиши.

        Args:
            idx (str): Индекс клавиши

        Returns:
            int: Базовый штраф для данной клавиши
        """
        return self.index_shtraf.get(idx, 0)

    def modifier_shtraf_for_symbol(self, ch: str, layout_name: str, mod_info: dict) -> int:
        """
        Рассчитать штраф за модификаторы для символа.

        Args:
            ch (str): Символ для анализа
            layout_name (str): Название раскладки
            mod_info (dict): Информация о модификаторах

        Returns:
            int: Суммарный штраф за модификаторы
        """
        shtraf = 0
        if mod_info.get("alt", False):
            shtraf += self.shtraf_config["alt_penalty"]
        if mod_info.get("ctrl", False):
            shtraf += self.shtraf_config["ctrl_penalty"]

        add_shift = False
        if mod_info.get("shift", False):
            add_shift = True
        else:
            if ch.isupper():
                explicit_shift_set = self.explicit_shift_syms.get(layout_name, set())
                if ch not in explicit_shift_set:
                    add_shift = True
        if add_shift:
            shtraf += self.shtraf_config["shift_penalty"]

        return shtraf

    def hand_label(self, finger: Optional[str]) -> str:
        """
        Определить метку руки по названию пальца.

        Args:
            finger (Optional[str]): Название пальца

        Returns:
            str: "L" для левой руки, "R" для правой, "" если не определено
        """
        if not finger:
            return ""
        return "L" if finger.startswith("lfi") else "R"

    def analyzeTextSync(self, text: str, layout: dict, progress, lock, batch: int = 50000) -> list:
        """
        Синхронный анализ текста для одной раскладки.

        Args:
            text (str): Текст для анализа
            layout (dict): Конфигурация раскладки
            progress: Объект прогресс-бара
            lock: Блокировка для потокобезопасности
            batch (int): Размер батча для обновления прогресса

        Returns:
            list: [layout_name, total_load, hand_switches, modifier_count, finger_stats]
        """
        total_load = 0
        finger_stats: Dict[Optional[str], int] = {}
        hand_switches = 0
        modifier_count = 0

        layout_name = layout.get("name", "Unknown")
        lookup = self.lookup_maps.get(layout_name, {})

        last_finger: Optional[str] = None
        last_hand: str = ""
        locally_count = 0

        for ch in text:
            if ch in {"\n", "\r", "\t"}:
                continue

            resolved = lookup.get(ch)
            if not resolved:
                continue

            idx, mod_info, finger = resolved
            if finger is None:
                finger_stats[None] = finger_stats.get(None, 0) + 1
                continue

            base = self.base_index_shtraf(idx)
            mods = self.modifier_shtraf_for_symbol(ch, layout_name, mod_info)
            effort = base + mods

            current_hand = self.hand_label(finger)
            if last_hand and current_hand and last_hand != current_hand:
                effort += self.shtraf_config["hand_switch_penalty"]
                hand_switches += 1

            if last_finger and finger and last_finger == finger:
                effort += self.shtraf_config["same_finger_penalty"]

            if mods > 0:
                modifier_count += 1

            total_load += effort
            finger_stats[finger] = finger_stats.get(finger, 0) + effort

            last_finger = finger
            last_hand = current_hand

            locally_count += 1
            if locally_count >= batch:
                with lock:
                    progress.update(locally_count)
                locally_count = 0

        if locally_count:
            with lock:
                progress.update(locally_count)

        return [layout_name, total_load, hand_switches, modifier_count, finger_stats]

    async def compareLayouts(self, text: str, layouts: dict, file_label: str = "Текст") -> list:
        """
        Асинхронный анализ текста для всех раскладок.

        Args:
            text (str): Текст для анализа
            layouts (dict): Словарь раскладок
            file_label (str): Метка файла для прогресс-бара

        Returns:
            list: Список результатов для каждой раскладки
        """
        n_layouts = sum(1 for name in layouts if name != "ШТРАФЫ")
        total_steps = len(text) * n_layouts
        progress = tqdm(total=total_steps,
                        desc=f"Общий прогресс ({file_label})",
                        unit="симв")
        lock = threading.Lock()

        tasks = []
        for name, lay in layouts.items():
            if name == "ШТРАФЫ":
                continue
            tasks.append(asyncio.to_thread(self.analyzeTextSync, text, lay, progress, lock))

        results_raw = await asyncio.gather(*tasks)
        progress.close()
        return results_raw

    async def analyze_csv(self, csv_file: str, layouts: dict) -> list:
        """
        Анализ CSV-файла с частотами биграмм.

        Args:
            csv_file (str): Путь к CSV-файлу
            layouts (dict): Словарь раскладок

        Returns:
            list: Список результатов для каждой раскладки
        """
        df = pd.read_csv(csv_file, header=None, sep=",")
        results = []
        for name, lay in layouts.items():
            if name == "ШТРАФЫ":
                continue
            total_load = 0
            finger_stats = {}
            hand_switches = 0
            modifier_count = 0
            lookup = self.lookup_maps.get(name, {})

            for _, row in df.iterrows():
                bigram = str(row[1])
                freq = int(row[2])
                for ch in bigram:
                    resolved = lookup.get(ch)
                    if not resolved:
                        continue
                    idx, mod_info, finger = resolved
                    base = self.base_index_shtraf(idx)
                    mods = self.modifier_shtraf_for_symbol(ch, name, mod_info)
                    effort = (base + mods) * freq
                    total_load += effort
                    finger_stats[finger] = finger_stats.get(finger, 0) + effort

            results.append([name, total_load, hand_switches, modifier_count, finger_stats])
        return results

    def analyze_words(self, text: str, layout_name: str) -> dict:
        """
        Анализирует распределение слов по рукам.

        Args:
            text (str): Текст для анализа
            layout_name (str): Название раскладки

        Returns:
            dict: Статистика по словам:
                - left_only: слова, набираемые только левой рукой
                - right_only: слова, набираемые только правой рукой
                - both: слова, набираемые обеими руками
        """
        stats = {"left_only": 0, "right_only": 0, "both": 0}
        words = text.split()

        lookup = self.lookup_maps.get(layout_name, {})

        for word in words:
            hands_used = set()
            for ch in word:
                resolved = lookup.get(ch)
                if not resolved:
                    continue
                _, _, finger = resolved
                if finger:
                    hand = "L" if finger.startswith("lfi") else "R"
                    hands_used.add(hand)

            if len(hands_used) == 1:
                if "L" in hands_used:
                    stats["left_only"] += 1
                else:
                    stats["right_only"] += 1
            elif len(hands_used) > 1:
                stats["both"] += 1

        return stats

    async def run_full_analysis(self) -> dict:
        """
        Запускает полный анализ всех корпусов текста.

        Анализирует:
            - Основной текст (data/voina-i-mir.txt)
            - Биграммы (data/digramms.txt)
            - 1-граммы (data/1grams-3.txt)
            - CSV с частотами (data/sortchbukw.csv)

        Returns:
            dict: Словарь с сырыми результатами для каждого корпуса:
                - text: результаты основного текста
                - digramms: результаты биграмм
                - onegramms: результаты 1-грамм
                - csv: результаты CSV-анализа
        """
        import unicodedata
        import os

        textFile = "data/voina-i-mir.txt"
        digramsFile = "data/digramms.txt"
        onegramsFile = "data/1grams-3.txt"
        csvFile = "data/sortchbukw.csv"

        # Инициализация раскладок
        await self.keybsInits()

        # --- Анализ основного текста ---
        with open(textFile, "r", encoding="utf-8") as f:
            text = unicodedata.normalize("NFC", f.read())
        results_text = await self.compareLayouts(text, self.layouts, file_label=os.path.basename(textFile))

        # добавляем статистику по словам для круговых диаграмм
        for res in results_text:
            layout_name = res[0]  # имя раскладки
            word_stats = self.analyze_words(text, layout_name)
            res.append(
                word_stats)  # теперь результат = [layout_name, total_load, hand_switches, modifier_count, finger_stats, word_stats]

        # --- Анализ биграмм ---
        with open(digramsFile, "r", encoding="utf-8") as f:
            digrams = [line.strip() for line in f.readlines()]
        text_digrams = "".join(digrams)
        results_digrams = await self.compareLayouts(text_digrams, self.layouts,
                                                    file_label=os.path.basename(digramsFile))

        # --- Анализ 1-грамм ---
        with open(onegramsFile, "r", encoding="utf-8") as f:
            onegrams = [line.strip() for line in f.readlines()]
        text_onegrams = "".join(onegrams)
        results_onegrams = await self.compareLayouts(text_onegrams, self.layouts,
                                                     file_label=os.path.basename(onegramsFile))

        # --- Анализ CSV ---
        results_csv = await self.analyze_csv(csvFile, self.layouts)

        # Сохраняем СЫРЫЕ результаты в память
        self.last_results = {
            "text": results_text,
            "digramms": results_digrams,
            "onegramms": results_onegrams,
            "csv": results_csv
        }

        return self.last_results
