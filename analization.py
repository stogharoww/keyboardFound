"""
Модуль для оценки удобства раскладок клавиатуры.
Измеряет удобство печати по трем параметрам:
1. Расстояние, которое проходят пальцы
2. Использование служебных клавиш (Shift, Alt, Ctrl)
3. Частоту переключения между левой и правой рукой

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
    ГЛАВНЫЙ КЛАСС - Анализатор раскладок клавиатуры.
     оценивает, насколько удобно печатать на разных раскладках.
    """

    def __init__(self,
                 shtraf_config: dict | None = None,
                 debug_mode: bool = False):
        """
        Настройка анализатора.

        shtraf_config - настройки штрафов (какие действия считаются сложными)
        debug_mode - режим отладки (показывать ли дополнительную информацию)
        """
        # Настройки штрафов за сложные действия
        self.shtraf_config = shtraf_config or {
            'shift_penalty':          2,  # штраф за Shift
            'alt_penalty':            3,  # штраф за Alt
            'ctrl_penalty':           4,  # штраф за Ctrl
            'same_finger_penalty':    1,  # штраф за повторное использование того же пальца
            'hand_switch_penalty':    1   # штраф за переключение между руками
        }
        self.debug_mode = debug_mode

        # Здесь будут храниться все раскладки клавиатур
        self.layouts: dict[str, dict] = {}

        # Вспомогательные карты - как "шпаргалки" для быстрого поиска
        self.index_shtraf: Dict[str, int] = {}  # штрафы для каждой клавиши
        self.sym_best: Dict[str, Dict[str, Tuple[str, dict]]] = {}  # лучшие варианты для символов
        self.idx_to_finger: Dict[str, Dict[str, str]] = {}  # какая клавиша какому пальцу принадлежит
        self.explicit_shift_syms: Dict[str, set] = {}  # символы, требующие Shift
        self.lookup_maps: Dict[str, Dict[str, Tuple[str, dict, str]]] = {}  # быстрый поиск по символам

        # Последние результаты анализа (чтобы не пересчитывать)
        self.last_results: dict = {}

    async def keybsInits(self):
        """
        Загружает все раскладки клавиатур и готовит их к анализу.
        """
        # Загружаем все раскладки из внешнего модуля
        self.layouts = await keyInitializations()

        # Создаем карту штрафов для каждой позиции клавиши
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

        # Для каждой раскладки создаем "шпаргалки" для быстрого поиска
        for name, lay in self.layouts.items():
            if name == "ШТРАФЫ":
                continue

            bukvaKey = lay.get("bukvaKey", {})
            modifierMap = lay.get("modifierMap", {})
            fingerKey = lay.get("fingerKey", {})

            # Создаем карту: номер клавиши -> палец
            idx_to_finger_map: Dict[str, str] = {}
            for finger, idxs in fingerKey.items():
                for idx in idxs:
                    idx_to_finger_map[idx] = finger
            self.idx_to_finger[name] = idx_to_finger_map

            # Находим лучший способ напечатать каждый символ
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

            # Создаем универсальную карту для быстрого поиска
            lookup = {}
            for s, (idx, info) in best_map.items():
                lookup[s] = (idx, info, idx_to_finger_map.get(idx))
                lookup[s.lower()] = (idx, info, idx_to_finger_map.get(idx))
            self.lookup_maps[name] = lookup

    def base_index_shtraf(self, idx: str) -> int:
        """
        Возвращает базовый штраф для клавиши по ее номеру.
        """
        return self.index_shtraf.get(idx, 0)

    def modifier_shtraf_for_symbol(self, ch: str, layout_name: str, mod_info: dict) -> int:
        """
        Считает штрафы за модификаторы (Shift, Alt, Ctrl).
        Как считать доплаты за дополнительные опции в заказе.
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
        Определяет, какой руке принадлежит палец.
        L - левая рука, R - правая рука.
        """
        if not finger:
            return ""
        return "L" if finger.startswith("lfi") else "R"

    def analyzeTextSync(self, text: str, layout: dict, progress, lock, batch: int = 50000) -> list:
        """
        Анализирует текст для одной раскладки.
        проверяет  - символ за символом.
        """
        total_load = 0  # общая нагрузка
        finger_stats: Dict[Optional[str], int] = {}  # статистика по пальцам
        hand_switches = 0  # количество переключений между руками
        modifier_count = 0  # количество использований модификаторов

        layout_name = layout.get("name", "Unknown")
        lookup = self.lookup_maps.get(layout_name, {})

        last_finger: Optional[str] = None  # последний использованный палец
        last_hand: str = ""  # последняя использованная рука
        locally_count = 0  # счетчик для обновления прогресса

        # Анализируем каждый символ в тексте
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

            # Проверяем переключение между руками
            current_hand = self.hand_label(finger)
            if last_hand and current_hand and last_hand != current_hand:
                effort += self.shtraf_config["hand_switch_penalty"]
                hand_switches += 1

            # Штраф за повторное использование того же пальца
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
        Сравнивает все раскладки на одном тексте.\
        """
        n_layouts = sum(1 for name in layouts if name != "ШТРАФЫ")
        total_steps = len(text) * n_layouts
        progress = tqdm(total=total_steps,
                        desc=f"Общий прогресс ({file_label})",
                        unit="симв")
        lock = threading.Lock()

        # Запускаем анализ для всех раскладок параллельно
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
        Анализирует CSV-файл с биграммами и частотами.
        Учитывает частоты использования - популярные комбинации влияют сильнее.
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

            # Анализируем каждую биграмму с учетом ее частоты
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
                    effort = (base + mods) * freq  # умножаем на частоту!
                    total_load += effort
                    finger_stats[finger] = finger_stats.get(finger, 0) + effort

            results.append([name, total_load, hand_switches, modifier_count, finger_stats])
        return results

    def analyze_words(self, text: str, layout_name: str) -> dict:
        """
        Анализирует, какой рукой печатаются слова.
        Показывает распределение нагрузки между руками.
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

            # Классифицируем слова по используемым рукам
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
        Запускает ПОЛНЫЙ АНАЛИЗ всех файлов.
        Главная функция - делает всю работу сразу.
        """
        import unicodedata
        import os

        # Файлы для анализа
        textFile = "data/voina-i-mir.txt"  # большой текст
        digramsFile = "data/digramms.txt"  # пары символов
        onegramsFile = "data/1grams-3.txt"  # одиночные символы
        csvFile = "data/sortchbukw.csv"    # CSV с частотами

        # Подготавливаем раскладки
        await self.keybsInits()

        # --- Анализ основного текста ---
        with open(textFile, "r", encoding="utf-8") as f:
            text = unicodedata.normalize("NFC", f.read())
        results_text = await self.compareLayouts(text, self.layouts, file_label=os.path.basename(textFile))

        # Добавляем статистику по словам для диаграмм
        for res in results_text:
            layout_name = res[0]
            word_stats = self.analyze_words(text, layout_name)
            res.append(word_stats)

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

        # Сохраняем все результаты
        self.last_results = {
            "text": results_text,
            "digramms": results_digrams,
            "onegramms": results_onegrams,
            "csv": results_csv
        }

        return self.last_results
