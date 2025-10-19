"""
Модуль для анализа эргономики раскладок клавиатуры.
Считает нагрузку по индексным штрафам, модификаторам и смене рук.
Предпочитает вариант символа с минимальным базовым штрафом (alt/shift),
не даёт None, но оставляет их для дебага.
"""

import asyncio
import unicodedata
from keyboardInit import keyInitializations
from tqdm import tqdm
import threading
from typing import Dict, Tuple, Optional


class TextAnalyzer:
    def __init__(self,
                 shtraf_config: dict | None = None,
                 debug_mode: bool = False):
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

    async def keybsInits(self):
        """Загрузка раскладок клавиатуры и построение карт."""
        self.layouts = await keyInitializations()

        # 1) Построить index_shtraf из раскладки "ШТРАФЫ"
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

        # 2) Для каждой реальной раскладки подготовить карты
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

    def _normalize(self, ch: str) -> str:
        return unicodedata.normalize("NFC", ch)

    def resolve_symbol(self, ch: str, layout_name: str) -> Optional[Tuple[str, dict, str]]:
        """Возвращает (idx, mod_info, finger) для символа."""
        s = self._normalize(ch)
        best_map = self.sym_best.get(layout_name, {})
        idx_to_finger_map = self.idx_to_finger.get(layout_name, {})

        if s in best_map:
            idx, info = best_map[s]
            return (idx, info, idx_to_finger_map.get(idx))

        s_lower = s.lower()
        if s_lower in best_map:
            idx, info = best_map[s_lower]
            return (idx, info, idx_to_finger_map.get(idx))

        return None

    def base_index_shtraf(self, idx: str) -> int:
        return self.index_shtraf.get(idx, 0)

    def modifier_shtraf_for_symbol(self, ch: str, layout_name: str, mod_info: dict) -> int:
        s = self._normalize(ch)
        shtraf = 0


        if mod_info.get("alt", False):
            shtraf += self.shtraf_config["alt_penalty"]
        if mod_info.get("ctrl", False):
            shtraf += self.shtraf_config["ctrl_penalty"]

        add_shift = False
        if mod_info.get("shift", False):
            add_shift = True
        else:
            if s.isupper():
                explicit_shift_set = self.explicit_shift_syms.get(layout_name, set())
                if s not in explicit_shift_set:
                    add_shift = True
        if add_shift:
            shtraf += self.shtraf_config["shift_penalty"]

        return shtraf

    def hand_label(self, finger: Optional[str]) -> str:
        if not finger:
            return ""
        return "L" if finger.startswith("lfi") else "R"

    def analyzeTextSync(self, text: str, layout: dict, progress, lock, batch: int = 5000) -> list:
        total_load = 0
        finger_stats: Dict[Optional[str], int] = {}
        hand_switches = 0
        modifier_count = 0
        unmapped: Dict[str, int] = {}

        layout_name = layout.get("name", "Unknown")

        last_finger: Optional[str] = None
        last_hand: str = ""
        locally_count = 0

        for ch in text:
            # Игнорируем служебные символы и мусор
            if ch in {"\n", "\r", "\t"}:
                continue

            resolved = self.resolve_symbol(ch, layout_name)
            if not resolved:
                # Символа нет в структуре данных (другая раскладка, латиница и т.п.) → игнорируем
                continue

            idx, mod_info, finger = resolved
            if finger is None:
                # Символ есть, но палец не назначен → дебаг
                unmapped[ch] = unmapped.get(ch, 0) + 1
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

        # 🔍 Отладка: выводим символы, которые не были распознаны (палец None)
        if unmapped:
            print(f"\n❗️ Символы без пальца в {layout_name}:")
            for sym, count in sorted(unmapped.items(), key=lambda x: -x[1])[:50]:
                print(f"   {repr(sym)} → {count} раз")

        return [layout_name, total_load, hand_switches, modifier_count, finger_stats]

    async def compareLayouts(self, text: str, layouts: dict) -> list:
        n_layouts = sum(1 for name in layouts if name != "ШТРАФЫ")
        total_steps = len(text) * n_layouts
        progress = tqdm(total=total_steps, desc="Общий прогресс", unit="симв")
        lock = threading.Lock()

        tasks = []
        for name, lay in layouts.items():
            if name == "ШТРАФЫ":
                continue
            tasks.append(asyncio.to_thread(self.analyzeTextSync, text, lay, progress, lock))

        results_raw = await asyncio.gather(*tasks)
        progress.close()
        return results_raw


    def returnResults(self, results: list) -> list:
        """Формирует результаты в структурированном виде без вывода на экран"""
        structured = []
        for res in results:
            layout_name, total_load, hand_switches, modifier_count, finger_stats = res

            # Добавляем нули для всех пальцев, чтобы они всегда были в выводе
            all_fingers = set(self.layouts[layout_name]["fingerKey"].keys())
            for f in all_fingers:
                if f not in finger_stats:
                    finger_stats[f] = 0

            structured.append({
                "layout_name": layout_name,
                "total_load": total_load,
                "hand_switches": hand_switches,
                "modifier_count": modifier_count,
                "finger_statistics": finger_stats
            })
        return structured
