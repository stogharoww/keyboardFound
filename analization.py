"""
Модуль для анализа эргономики раскладок клавиатуры.
Содержит класс TextAnalyzer с методами для оценки усилий при наборе текста
на различных раскладках клавиатуры.
"""

import asyncio
import unicodedata
from keyboardInit import keyInitializations
from tqdm import tqdm
import threading
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor
import multiprocessing


class TextAnalyzer:
    def __init__(self,
                 shtraf_config: dict | None = None,
                 debug_mode: bool = False):
        """Инициализация анализатора с настройкой штрафов и режима отладки"""
        self.shtraf_config = shtraf_config or {
            'base_key_effort':        1,
            'shift_penalty':          2,
            'alt_penalty':            3,
            'ctrl_penalty':           4,
            'combo_penalty':          5,
            'same_finger_penalty':    1,
            'hand_switch_penalty':    1,
            'weak_finger_penalty':    1
        }
        self.debug_mode = debug_mode
        self.layouts: dict[str, dict] = {}

    async def keybsInits(self):
        """Загрузка и предобработка раскладок клавиатуры"""
        self.layouts = await keyInitializations()
        for name, lay in list(self.layouts.items()):
            lay.setdefault("name", name)
            bukva = lay.get("bukvaKey", {})
            finger_map = lay.get("fingerKey", {})
            sym_to_key = {}
            for key_idx, syms in bukva.items():
                for s in syms:
                    s_n = unicodedata.normalize("NFC", s)
                    sym_to_key[s_n] = key_idx
            sym_to_finger = {}
            for finger, keys in finger_map.items():
                for k in keys:
                    for sym, key in sym_to_key.items():
                        if key == k:
                            sym_to_finger[sym] = finger
            lay["_sym_to_key"] = sym_to_key
            lay["_sym_to_finger"] = sym_to_finger
            if "modifierMap" in lay:
                mm = {}
                for k, v in lay["modifierMap"].items():
                    mm[unicodedata.normalize("NFC", k)] = v
                lay["modifierMap"] = mm
            if "modifiers" in lay:
                lay["modifiers"] = set(unicodedata.normalize("NFC", m) for m in lay.get("modifiers", []))

    def getSymbolFinger(self, char: str, layout=None) -> str | None:
        """Определяет палец для нажатия символа в заданной раскладке"""
        s = unicodedata.normalize("NFC", char)

        if isinstance(layout, dict):
            layouts_iter = [("custom", layout)]
        elif isinstance(layout, str):
            layouts_iter = [(layout, self.layouts.get(layout, {}))]
        else:
            wanted = ("qwerty", "vizov", "yaverty")
            layouts_iter = [
                (name, self.layouts[name])
                for name in wanted if name in self.layouts
            ]

        for _, lay in layouts_iter:
            bukva = lay.get("bukvaKey", {})
            finger_map = lay.get("fingerKey", {})

            found_key = None
            for key_idx, symbols in bukva.items():
                for sym in symbols:
                    if unicodedata.normalize("NFC", sym) == s:
                        found_key = key_idx
                        break
                if found_key is not None:
                    break

            if found_key is None:
                continue

            for finger, keys in finger_map.items():
                if found_key in keys:
                    return finger

        return None

    @lru_cache(maxsize=4096)
    def cachedSymbolFinger(self, char: str, layout_name: str) -> str | None:
        """Кэшированная версия определения пальца для символа"""
        layout = self.layouts[layout_name]
        return self.getSymbolFinger(char, layout)

    def getSumbolKey(self, char: str, layout: dict) -> str | None:
        """Определяет клавишу для символа в раскладке"""
        s = unicodedata.normalize("NFC", char)
        bukva = layout.get("bukvaKey", {})

        for key_idx, symbols in bukva.items():
            for sym in symbols:
                sym_str = unicodedata.normalize("NFC", sym)
                if sym_str.startswith(("shift+", "alt+")):
                    candidate = sym_str.split("+", 1)[1]
                else:
                    candidate = sym_str
                if candidate == s:
                    return key_idx

        return None

    def getModifierShtraf(self, char: str, layout: dict) -> int:
        """Рассчитывает штраф за использование модификаторов"""
        s = unicodedata.normalize("NFC", char)
        mod_info = layout.get("modifierMap", {}).get(s, {})
        shtraf = 0

        if s.isupper() or mod_info.get("shift", False):
            shtraf += self.shtraf_config["shift_penalty"]

        if mod_info.get("alt", False):
            shtraf += self.shtraf_config["alt_penalty"]

        if mod_info.get("ctrl", False):
            shtraf += self.shtraf_config["ctrl_penalty"]

        combo = mod_info.get("combo", 0)
        if combo:
            shtraf += self.shtraf_config["combo_penalty"] * combo

        return shtraf

    def changeHand(self, current_finger: str | None, previous_finger: str | None) -> int:
        """Рассчитывает штраф за смену руки при наборе"""
        if not current_finger or not previous_finger:
            return 0

        current_hand = "L" if current_finger.startswith("lfi") else "R"
        previous_hand = "L" if previous_finger.startswith("lfi") else "R"

        if current_hand != previous_hand:
            return self.shtraf_config["hand_switch_penalty"]

        return 0

    def calculateDistanceShtraf(self, char: str,
                                layout: dict,
                                last_hand: dict) -> int:
        """Рассчитывает штраф за расстояние между последовательными клавишами"""
        prev_idx = last_hand.get("last_key_index")
        curr_idx = self.getSumbolKey(char, layout)

        if prev_idx is None or curr_idx is None:
            last_hand["last_key_index"] = curr_idx
            return 0

        try:
            dist = abs(int(curr_idx) - int(prev_idx))
            last_hand["last_key_index"] = curr_idx
            if dist > 3:
                return min(dist - 3, 5)
        except ValueError:
            last_hand["last_key_index"] = curr_idx

        return 0

    def calculateEffort(self, char: str,
                        layout: dict,
                        last_hand: dict) -> tuple[int, str]:
        """Суммирует все штрафы для символа и возвращает общее усилие и руку"""
        if not char.strip():
            return 0, last_hand.get("hand", "")

        total = self.shtraf_config["base_key_effort"]
        total += self.getModifierShtraf(char, layout)
        layout_name = layout.get("name", "Unknown")
        finger = self.cachedSymbolFinger(char, layout_name)
        hand = finger[0] if finger else "r"

        total += self.changeHand(hand, last_hand.get("hand", ""))
        if finger and last_hand.get("finger") == finger:
            total += self.shtraf_config["same_finger_penalty"]
        if finger and finger.endswith("pi"):
            total += self.shtraf_config["weak_finger_penalty"]

        total += self.calculateDistanceShtraf(char, layout, last_hand)

        last_hand["hand"] = hand
        last_hand["finger"] = finger

        if self.debug_mode:
            print(f"{char!r}: total={total}, finger={finger}, hand={hand}")

        return total, hand

    def calculateEffortSymbol(self, char: str, layout: dict,
                              last_hand: dict) -> tuple[int, str]:
        """Алиас для calculateEffort с сохранением сигнатуры"""
        return self.calculateEffort(char, layout, last_hand)

    def calculateEffortFinger(self, finger: str, layout: dict,
                              calculateEffortSymb: dict) -> int:
        """Суммирует штрафы по конкретному пальцу"""
        return sum(stats.get(finger, 0) for stats in calculateEffortSymb.values())

    @lru_cache(maxsize=4096)
    def cachedEffort(self, char: str, layout_name: str) -> int:
        """Кэшированная версия расчета усилий для символа"""
        layout = self.layouts[layout_name]
        dummy_hand = {"hand": "", "finger": "", "last_key_index": None}
        effort, _ = self.calculateEffort(char, layout, dummy_hand)
        return effort

    def analyzeTextSync(self, text: str, layout: dict, progress, lock, batch: int = 5000) -> dict:
        """Синхронный анализ текста для одной раскладки с прогресс-баром"""
        print(f"🚀 Запуск анализа: {layout.get('name')}")
        total_load = 0
        finger_stats = {}
        hand_switches = 0
        modifier_count = 0
        last_hand = {"hand": "", "finger": "", "last_key_index": None}

        locally_count = 0
        layout_name = layout.get("name", "Unknown")

        for i, ch in enumerate(text):
            effort = self.cachedEffort(ch, layout_name)
            finger = self.cachedSymbolFinger(ch, layout_name)
            hand = finger[0] if finger else "r"

            total_load += effort
            finger_stats[finger] = finger_stats.get(finger, 0) + 1

            if hand != last_hand.get("hand"):
                hand_switches += 1

            last_hand["hand"] = hand
            last_hand["finger"] = finger

            locally_count += 1
            if locally_count >= batch:
                with lock:
                    progress.update(locally_count)
                locally_count = 0

        if locally_count:
            with lock:
                progress.update(locally_count)

        print(f"✅ Завершён анализ: {layout_name}")
        return {
            "total_load": total_load,
            "finger_statistics": finger_stats,
            "hand_switches": hand_switches,
            "modifier_count": modifier_count,
            "layout_name": layout_name
        }

    async def compareLayouts(self, text: str, layouts: dict) -> dict:
        """Сравнивает эффективность нескольких раскладок на заданном тексте"""
        n_layouts = sum(1 for name in layouts if name != "ШТРАФЫ")
        total_steps = len(text) * n_layouts
        progress = tqdm(total=total_steps, desc="Общий прогресс", unit="симв")
        lock = threading.Lock()

        tasks = []
        layout_names = []
        for name, lay in layouts.items():
            if name == "ШТРАФЫ":
                continue
            layout_names.append(name)
            tasks.append(asyncio.to_thread(self.analyzeTextSync, text, lay, progress, lock))

        results_raw = await asyncio.gather(*tasks)
        progress.close()
        return dict(zip(layout_names, results_raw))

    def returnResults(self, result: dict) -> None:
        """Выводит результаты сравнительного анализа раскладок"""
        for name, stats in result.items():
            print(f"=== Layout: {name} ===")
            for k, v in stats.items():
                print(f"{k}: {v}")
            print()
