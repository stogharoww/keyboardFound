from keyboardInit import keyInitializations
import pandas as pd
import asyncio
import aiofiles
import unicodedata


class TextAnalyzer:
    def __init__(self):
        """
        хз пробел, тут что-то надо чисто чтобы заполнить и всё. Если будет нужно, используйте
        """

    async def keybsInits(self):
        self.layouts = await keyInitializations()


    def getSymbolFinger(self, char: str, layout=None) -> str | None:
        """
        Определяет, каким пальцем нажимается символ.
        :param char: анализируемый символ
        :param layout: словарь раскладки, имя раскладки или None
        :return: строка с идентификатором пальца (например, 'lfi2') или None
        """
        s = unicodedata.normalize("NFC", str(char))

        # Подготовка итератора раскладок
        if isinstance(layout, dict):
            layouts_iter = (("custom", layout),)
        else:
            all_layouts = getattr(self, "layouts", {}) or {}
            if isinstance(layout, str):
                if layout not in all_layouts:
                    return None
                layouts_iter = ((layout, all_layouts[layout]),)
            else:
                wanted = ("qwerty", "vizov", "yaverty")
                layouts_iter = ((name, all_layouts[name]) for name in wanted if name in all_layouts)

        # По каждой раскладке ищем индекс клавиши, потом палец
        for layout_name, lay in layouts_iter:
            if not lay:
                continue
            bukva = lay.get("bukvaKey", {}) or {}

            found_key = None
            for key_idx, symbols in bukva.items():
                for sym in symbols:
                    sym_norm = unicodedata.normalize("NFC", str(sym))
                    if sym_norm == s or sym_norm.lower() == s.lower() or sym_norm.upper() == s.upper():
                        found_key = str(key_idx)
                        break
                if found_key is not None:
                    break

            if found_key is None:
                continue

            finger_map = lay.get("fingerKey", {}) or {}
            for finger, key_idxs in finger_map.items():
                for k in key_idxs:
                    if str(k) == found_key:
                        return finger

            # индекс найден в bukvaKey, но нет соответствия в fingerKey для этой раскладки
            return None

        return None

    def getSumbolKey(self, char: str, layout: dict) -> str | None:
        """
        Определяет, на какой клавише находится символ
        :param char: анализируемый символ
        :param layout: словарь раскладки с bukvaKey
        :return: строка с индексом клавиши (например, '16') или None если не найдено
        """
        import unicodedata

        s = unicodedata.normalize("NFC", str(char))

        bukva = layout.get("bukvaKey", {}) or {}
        # Перебираем пары key_idx -> symbols
        for key_idx, symbols in bukva.items():
            for sym in symbols:
                sym_str = unicodedata.normalize("NFC", str(sym))

                # Учесть варианты с модификаторами вида "shift+X" или "alt+X"
                if "+" in sym_str and (sym_str.startswith("shift+") or sym_str.startswith("alt+")):
                    candidate = sym_str.split("+", 1)[1]
                else:
                    candidate = sym_str

                # Сравниваем точь-в-точь и по регистру
                if candidate == s or candidate.lower() == s.lower() or candidate.upper() == s.upper():
                    return str(key_idx)

        return None

    def getModifierShtraf(self, char: str, layout: dict) -> int:
        """
        Проверяет, требует ли символ нажатия модификаторов (SHIFT, ALT, CTRL)
        и возвращает соответствующий штраф.

        :param char: анализируемый символ (например, 'A', '$', '€')
        :param layout: словарь раскладки с ключом 'modifierMap'
        :return: целое число — сумма штрафов за модификаторы
        """
        # Если в раскладке нет информации о модификаторах, штраф 0
        if 'modifierMap' not in layout:
            return 0

        shtraf = 0
        modifiers = layout['modifierMap']

        # Штраф за SHIFT
        if char.isupper():
            shtraf += self.shtraf_config['shift_penalty']
            print(f"Символ '{char}': SHIFT штраф +{self.shtraf_config['shift_penalty']}")

        elif char in modifiers:
            modifier_info = modifiers[char]

            # Если символ явно требует SHIFT (например, '$', '%', '&')
            if 'shift' in modifier_info and modifier_info['shift']:
                shtraf += self.shtraf_config['shift_penalty']
                print(f"Символ '{char}': SHIFT штраф +{self.shtraf_config['shift_penalty']}")

            # Если символ требует ALT

        if 'alt' in modifier_info and modifier_info['alt']:
            shtraf += self.shtraf_config['alt_penalty']
            print(f"Символ '{char}': ALT штраф +{self.shtraf_config['alt_penalty']}")

            # Если символ требует CTRL
        if 'ctrl' in modifier_info and modifier_info['ctrl']:
            shtraf += self.shtraf_config['ctrl_penalty']
            print(f"Символ '{char}': CTRL штраф +{self.shtraf_config['ctrl_penalty']}")

            # Если символ требует комбинации модификаторов
        if 'combo' in modifier_info:
            combo_count = modifier_info['combo']
            shtraf += self.shtraf_config['combo_penalty'] * combo_count
            print(f"Символ '{char}': COMBO штраф +{self.shtraf_config['combo_penalty'] * combo_count}")

        elif char.isdigit():
            # Проверяем, требует ли цифра модификатора в данной раскладке
            if char in modifiers:
                modifier_info = modifiers[char]
                if 'shift' in modifier_info:
                    shtraf += self.shtraf_config['shift_penalty']

        return shtraf

    def changeHand(self, current_hand: str, previous_hand: str) -> int:
        """
        Сравнивает текущую и предыдущую руку, если r поменялось на l или наоборот, то +1 штраф.

        :param current_hand: текущая рука ('l' - левая, 'r' - правая)
        :param previous_hand: предыдущая рука ('l' - левая, 'r' - правая)
        :return: штраф за смену руки (1 или 0)
        """
        # Если первый символ в тексте - штрафа нет
        if not previous_hand:
            return 0

        # Если текущая рука не определена - штрафа нет
        if not current_hand:
            return 0

        # приводим к нижнему регистру
        prev_hand = previous_hand.lower().strip()
        curr_hand = current_hand.lower().strip()

        valid_hands = ['l', 'r']
        if prev_hand not in valid_hands or curr_hand not in valid_hands:
            return 0

        # штраф за смену руки
        if prev_hand != curr_hand:
            return self.shtraf_config['hand_switch_penalty']

        return 0

    def calculateEffort(self, char: str, layout: dict, last_hand: dict) -> tuple[int, str]:
        """
        Суммирует ВСЕ штрафы для одного символа и определяет текущую активную руку.

        :param char: анализируемый символ
        :param layout: словарь раскладки клавиатуры
        :param last_hand: словарь с информацией о предыдущем состоянии {'hand': 'l', 'finger': 'lfi'}
        :return: кортеж (общий_штраф, текущая_рука)
        """

        if not char.strip():
            return 0, last_hand.get('hand', '')

        total_effort = 0
        debug_info = []  # Для отладки

        base_effort = self.shtraf_config['base_key_effort']
        total_effort += base_effort
        debug_info.append(f"База: +{base_effort}")

        # ШТРАФ ЗА МОДИФИКАТОРЫ (Shift, Alt, Ctrl)
        modifier_shtraf = self.getModifierShtraf(char, layout)
        total_effort += modifier_shtraf
        if modifier_shtraf > 0:
            debug_info.append(f"Модификаторы: +{modifier_shtraf}")

        # ОПРЕДЕЛЯЕМ ТЕКУЩИЙ ПАЛЕЦ И РУКУ
        current_finger = self.getSymbolFinger(char, layout)

        if current_finger == 'unknown':
            # Если палец не определен, используем правую руку по умолчанию
            current_hand = 'r'
            debug_info.append("Палец: неизвестен (рука по умолчанию: правая)")
        else:
            # Первая буква идентификатора пальца указывает на руку (l/r)
            current_hand = current_finger[0] if current_finger else 'r'
            debug_info.append(f"Палец: {current_finger}, Рука: {current_hand}")

        # ШТРАФ ЗА СМЕНУ РУКИ
        previous_hand = last_hand.get('hand', '')
        hand_change_shtraf = self.changeHand(current_hand, previous_hand)
        total_effort += hand_change_shtraf
        if hand_change_shtraf > 0:
            debug_info.append(f"Смена руки: +{hand_change_shtraf}")

        # ШТРАФ ЗА ПОВТОРЕНИЕ ПАЛЬЦА
        previous_finger = last_hand.get('finger', '')
        same_finger_shtraf = 0

        if (previous_finger and current_finger != 'unknown' and
                previous_finger == current_finger):
            same_finger_shtraf = self.shtraf_config['same_finger_penalty']
            total_effort += same_finger_shtraf
            debug_info.append(f"Повтор пальца: +{same_finger_shtraf}")

        # ШТРАФ ЗА мизинцы
        weak_finger_shtraf = 0
        if current_finger.endswith('pi'):  # Мизинцы (pinky fingers)
            weak_finger_shtraf = self.shtraf_config['weak_finger_penalty']
            total_effort += weak_finger_shtraf
            debug_info.append(f"Слабый палец: +{weak_finger_shtraf}")

        # ШТРАФ ЗА РАССТОЯНИЕ (если есть данные о позициях клавиш)
        distance_shtraf = self.calculateDistanceShtraf(char, layout, last_hand)
        total_effort += distance_shtraf
        if distance_shtraf > 0:
            debug_info.append(f"Расстояние: +{distance_shtraf}")

        # ОБНОВЛЯЕМ ИНФОРМАЦИЮ О ПОСЛЕДНЕЙ РУКЕ
        last_hand['hand'] = current_hand
        last_hand['finger'] = current_finger
        last_hand['last_char'] = char  # Сохраняем последний символ для отладки

        if self.debug_mode:
            print(f"'{char}': {total_effort} = {', '.join(debug_info)}")

        return total_effort, current_hand

    def calculateDistanceShtraf(self, char: str, layout: dict, last_hand: dict) -> int:

        if 'keyPositions' not in layout or 'last_key_index' not in last_hand:
            return 0

        current_key_index = self.getSumbolKey(char, layout)
        previous_key_index = last_hand.get('last_key_index')

        if not previous_key_index or current_key_index == 'unknown':
            last_hand['last_key_index'] = current_key_index
            return 0

        # если клавиши далеко друг от друга - штраф
        try:
            prev_idx = int(previous_key_index)
            curr_idx = int(current_key_index)
            distance = abs(curr_idx - prev_idx)

            if distance > 3:  # Если клавиши сильно разнесены
                last_hand['last_key_index'] = current_key_index
                return min(distance - 3, 5)  # Максимум 5 штрафных очков
        except (ValueError, TypeError):
            pass

        last_hand['last_key_index'] = current_key_index
        return 0

    def calculateEffortSymbol(self, char: str, layout: dict, last_hand: dict) -> tuple[int, str]:
        """
        Суммирует все штрафы для символа:
        - за клавишу
        - за модификаторы
        - за смену руки
        :param char: анализируемый символ
        :param layout: словарь раскладки
        :param last_hand: словарь с последней активной рукой
        :return: кортеж (общий штраф, текущая рука)
        """

    def calculateEffortFinger(self, finger: str, layout: dict, calculateEffortSymb: dict):
        """
        Суммирует все штрафы по конкретному пальцу
        :param finger:
        :param layout:
        :param calculateEffortSymb:
        :return:
        """

    def analyzeText(self, text: str, layout: dict) -> dict:
        """
        Проходит по тексту и вычисляет:
        - общую нагрузку
        - нагрузку по пальцам
        - количество смен рук
        - количество модификаторов
        :param text: строка текста для анализа
        :param layout: словарь раскладки
        :return: словарь с результатами анализа
        """
        total_load = 0
        finger_statistics = {finger: 0 for finger in self.fingerKey.keys()}
        hand_switches = 0
        modifier_count = 0

        last_hand = None  # Хранит информацию о последней использованной руке

        for char in text:
            # Проверяем, является ли символ модификатором (например, Shift, Ctrl и т.д.)
            if char in layout.get('modifiers', []):
                modifier_count += 1
                continue  # Пропускаем модификаторы при подсчете нагрузки

            # Находим соответствующий ключ для символа
            for key, bukvas in self.bukvaKey.items():
                if char in bukvas:
                    total_load += 1  # Увеличиваем общую нагрузку
                    finger_used = None

                    # Определяем, какой палец использован для данного символа
                    for finger, keys in self.fingerKey.items():
                        if key in keys:
                            finger_statistics[finger] += 1
                            finger_used = finger
                            break

                    # Определяем, какая рука используется (левая или правая)
                    current_hand = 'left' if finger_used in self.left_fingers else 'right'

                    # Проверяем смену рук
                    if last_hand and last_hand != current_hand:
                        hand_switches += 1

                    last_hand = current_hand  # Обновляем последнюю использованную руку

        return {
            'total_load': total_load,
            'finger_statistics': finger_statistics,
            'hand_switches': hand_switches,
            'modifier_count': modifier_count,
            'layout_name': layout.get('name', 'Unknown Layout')  # Добавляем имя раскладки, если доступно
        }



    def compareLayouts(self, text: str, layouts: dict) -> dict:
        """
        Запускает анализы для каждой раскладки и текста и собирает сравнительную статистику,
        собирает значения для каждого пальца.
        Это финальная логическая функция, которая реально что-то считает
        :param text: строка текста для анализа
        :param layouts: словарь всех раскладок
        :return: словарь с результатами по каждой раскладке
        """
        results = {}

        for layout_name, layout_data in layouts.items():
            matrix = layout_data['matrix']
            symbols = layout_data['symbols']

            # Создаем новый экземпляр Cortages для каждой раскладки
            cortages_instance = Cortages(matrix, symbols, layout_name)
            asyncio.run(cortages_instance.initialize())  # Инициализируем раскладку

            # Статистика по пальцам
            finger_statistics = {finger: 0 for finger in cortages_instance.fingerKey.keys()}

            for char in text:
                # Находим соответствующий ключ для символа
                for key, bukvas in cortages_instance.bukvaKey.items():
                    if char in bukvas:
                        # Определяем, какой палец использован для данного символа
                        for finger, keys in cortages_instance.fingerKey.items():
                            if key in keys:
                                finger_statistics[finger] += 1
                                break

            results[layout_name] = {
                'finger_statistics': finger_statistics,
                'total_chars': len(text),
                'layout_name': layout_name
            }

        return results


    def returnResults(self, result: dict) -> None:
        """
        Функция, которая создана исключительно только для вывода финальных результатов для графиков
        выводит нагрузки по каждому пальцу
        Форматирует и выводит результаты анализа:
        - нагрузка по пальцам
        - общая нагрузка
        - модификаторы
        - смены рук
        :param result: словарь с результатами анализа
        :return: None
        """
