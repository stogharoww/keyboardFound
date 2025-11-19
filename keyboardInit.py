"""
Модуль для создания и инициализации раскладок клавиатуры.
Содержит классы для разделения клавиш по рукам и создания структур данных раскладок.
"""

import asyncio
import aiofiles
import pandas as pd

class CreatorBase:
    """Класс, разделяющий клавиши на правую и левую руку"""
    def __init__(self, matrix):
        self.matrix = matrix

    def split(self):
        left = []
        right = []
        for i, row in enumerate(self.matrix):
            if i == 0:
                left.append(row[:6])
                right.append(row[6:])
            else:
                left.append(row[:5])
                right.append(row[5:])
        return left, right


class Cortages(CreatorBase):
    def __init__(self, matrix, symbols, layout_name):
        self.matrix = matrix
        self.symbols = symbols
        self.layout_name = layout_name

        self.fingerKey = {}     # палец → индексы
        self.bukvaKey = {}      # индекс → символы
        self.bukvaFinger = {}   # символ → палец
        self.shtrafKey = {}
        self.fingerShtraf = {}
        self.sym_to_finger = {}
        self.modifierMap = {}

    async def create_tuples(self):
        """Формируем карту пальцев"""
        left, right = self.split()
        abj_left = left.copy()
        abj_left[0] = abj_left[0][1:]

        # Левая рука
        self.fingerKey["lfi5"] = ('41', '02', '16', '30', '44')
        self.fingerKey["lfi4"] = tuple(row[1] for row in abj_left if len(row) > 1)
        self.fingerKey["lfi3"] = tuple(row[2] for row in abj_left if len(row) > 2)
        self.fingerKey["lfi2"] = tuple(idx for row in abj_left for idx in row[3:5] if len(row) >= 5)

        # Правая рука
        self.fingerKey["rfi2"] = tuple(idx for row in right for idx in row[3:5] if len(row) >= 5)
        self.fingerKey["rfi3"] = tuple(row[2] for row in right if len(row) > 2)
        self.fingerKey["rfi4"] = tuple(row[3] for row in right if len(row) > 3)
        self.fingerKey["rfi5"] = ('11', '12', '13', '25', '26', '27', '43', '39', '40', '53')

        self.fingerKey["lfi2"] += ('21', '22')  # н, г
        self.fingerKey["lfi3"] += ('35', '36')  # р, о
        self.fingerKey["rfi2"] += ('49', '50')  # т, ь
        self.fingerKey["lfi5"] += ('2',)  # 1
        self.fingerKey["rfi5"] += ('7', '8')  # 6, 7

        # Модификаторы
        self.fingerKey["lfi1"] = ('SHIFT42', 'ALT56')

        await asyncio.sleep(0)

    async def process_bukva_index(self):
        """Формируем карту индекс → символы"""
        self.modifierMap = {}

        for row_idx, row in enumerate(self.symbols):
            pointer = 0
            last_key = None

            for tok in row:
                if pointer >= len(self.matrix[row_idx]):
                    break

                idx = self.matrix[row_idx][pointer]

                # обычный символ
                if not tok.startswith(('shift+', 'alt+')):
                    self.bukvaKey.setdefault(idx, [])
                    symbols = [tok, tok.upper()] if tok.islower() else [tok]
                    for s in symbols:
                        if s not in self.bukvaKey[idx]:
                            self.bukvaKey[idx].append(s)
                            self.modifierMap[s] = {'shift': False, 'alt': False}
                    last_key = idx
                    pointer += 1
                    continue

                # shift
                if tok.startswith('shift+'):
                    sym = tok.split('+', 1)[1]
                    self.bukvaKey.setdefault(last_key, [])
                    if sym not in self.bukvaKey[last_key]:
                        self.bukvaKey[last_key].append(sym)
                        self.modifierMap[sym] = {'shift': True, 'alt': False}
                    continue


                # alt
                if tok.startswith('alt+'):
                    sym = tok.split('+', 1)[1]
                    pair = [sym, sym.upper()] if sym.islower() else [sym]
                    self.bukvaKey.setdefault(last_key, [])
                    for s in pair:
                        if s not in self.bukvaKey[last_key]:
                            self.bukvaKey[last_key].append(s)
                            self.modifierMap[s] = {'shift': False, 'alt': True}
                    continue

        await asyncio.sleep(0)

    async def initialize(self):
        await self.create_tuples()
        await self.process_bukva_index()

        # Символ → палец
        self.sym_to_finger = {}
        for finger, key_ids in self.fingerKey.items():
            for key_id in key_ids:
                for sym in self.bukvaKey.get(key_id, []):
                    self.sym_to_finger[sym] = finger


def massiveList():
    matrix = [
        ['41', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'],
        ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '43'],
        ['30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40'],
        ['44', '45', '46', '47', '48', '49', '50', '51', '52', '53']
    ]

    # раскладки
    yaverty = [
        ['ю', '1', 'shift+!', '2', 'shift+@', '3', 'shift+ё', '4', 'shift+Ё', '5', 'shift+ъ',
         '6', 'shift+ъ', '7', 'shift+&', '8', 'shift+*', '9', 'shift+(', '0', 'shift+)', '-', 'shift+_', 'ч'],
        ['я', 'в', 'е', 'р', 'т', 'ы', 'у', 'и', 'о', 'п', 'ш', 'щ', 'э'],
        ['а', 'с', 'д', 'ф', 'г', 'х', 'й', 'к', 'л', ';', 'shift+:', '--', 'shift+"'],
        ['з', 'ь', 'ц', 'ж', 'б', 'н', 'м', ',', 'shift+<', '.', 'shift+>', '/', 'shift+?']
    ]

    vizov = [
        ['ю', 'ё', '7', 'shift+[', '5', 'shift+{', '3', 'shift+}', '1', 'shift+(', '9', 'shift+=', '0',
         'shift+*', '2', 'shift+)', '4', 'shift++', '6', 'shift+]', '8', 'shift+!', 'щ'],
        ['б', 'ы', 'о', 'у', 'alt+ю', 'ь', 'ё', 'л', 'д', 'я', 'г', 'ж', 'ц'],
        ['ъ', 'ч', 'alt+ц', 'и', 'е', 'alt+э', 'а', ',', 'shift+;', '.', 'shift+:', 'н', 'alt+щ'],
        ['т', 'alt+ъ', 'с', 'в', 'з', 'ш', 'х', 'й', 'к', '_', 'shift+-', 'э', 'р']
    ]

    qwerty = [
        ['ё', '1', 'shift+!', '2', 'shift+"', '3', 'shift+№', '4', 'shift+;', '5', 'shift+%', '6', 'shift+:', '7',
         'shift+?', '8', 'shift+*', '9', 'shift+(', '0', 'shift+)', '-', 'shift+_', '=', 'shift++'],
        ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ'],
        ['ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э'],
        ['я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю', '.']
    ]

    shtrafs = [
        ['6', '5', '4', '4', '4', '4', '4', '4', '4', '4', '4', '5', '6'],
        ['3', '2', '2', '2', '2', '2', '2', '2', '2', '2', '3', '5', '6'],
        ['0', '0', '0', '0', '1', '1', '0', '0', '0', '0', '1'],
        ['2', '2', '2', '2', '3', '3', '2', '2', '2', '2']
    ]

    ant = [
        ['\\', 'shift+-', '!', 'shift+9', '?', 'shift+7', '`', 'shift+5', '"', 'shift+3', '=', 'shift+1',
         '+', 'shift+0', '-', 'shift+2', '*', 'shift+4', '/', 'shift+6', '%', 'shift+8', '(', 'shift+«', ')',
         'shift+»'],
        ['Г', 'П', 'Р', 'Д', 'М', 'Ы', 'И', 'Я', 'У', 'Х', 'Ц', 'Ж', 'Ч'],
        ['В', 'Н', 'С', 'Т', 'Л', 'Ь', 'О', 'Е', 'А', 'К', 'З'],
        ['Щ', 'Й', 'Ш', 'Б', ',', 'shift+;', '.', 'shift+:', 'Ю', 'Э', 'Ё', 'Ф']
    ]

    skoropis = [
        ['*', '.', 'ё', 'ъ', '?', '!', '-', '(', ')', '__', '«'],
        ['ц', 'ь', 'я', ',', '.', 'з', 'в', 'к', 'д', 'ч', 'ш', 'щ', "'", '"'],
        ['у', 'и', 'е', 'о', 'а', 'л', 'н', 'т', 'с', 'р', 'й'],
        ['ф', 'э', 'ч', 'ы', 'ю', 'б', 'м', 'п', 'г', 'ж']
    ]

    zubachew = [
        ['Ё', '1', 'shift+!', '2', 'shift+"', '3', 'shift+№', '4', 'shift+;', '5', 'shift+%', '6', 'shift+:',
         '7', 'shift+?', '8', 'shift+*', '9', 'shift+(', '0', 'shift+)', '-', 'shift+_', '=', 'shift++'],
        ['Ф', 'Ы', 'А', 'Я', ',', 'Ъ', 'Й', 'М', 'З', 'П', 'Х', 'Ц', 'Щ', '\\', 'shift+/'],
        ['Г', 'И', 'Е', 'О', 'У', 'Л', 'Т', 'С', 'Н', 'З', 'Ж'],
        ['Ш', 'ь', 'shift+Ъ', 'Ю', '.', 'shift+Ь', 'Э', 'Б', 'Д', 'В', 'К', 'Ч']
    ]

    diktor = [
        ['Ё', '1', 'shift+Ъ', '2', 'shift+Ь', '3', 'shift+№', '4', 'shift+%', '5', 'shift+:', '6', 'shift+;',
         '7', 'shift+-', '8', 'shift+"', '9', 'shift+(', '0', 'shift+)', '*', 'shift+-', '=', 'shift++'],
        ['Ц', 'ь', 'shift+ъ', 'Я', ',', 'shift+?', '.', 'shift+!', 'З', 'В', 'К', 'Д', 'Ч', 'Ш', 'Щ'],
        ['У', 'И', 'Е', 'О', 'А', 'Л', 'Н', 'Т', 'С', 'Р', 'Й'],
        ['Ф', 'Э', 'Х', 'Ы', 'Ю', 'Б', 'М', 'П', 'Г', 'Ж']
    ]

    return matrix, yaverty, vizov, qwerty, shtrafs, ant, skoropis, zubachew, diktor




async def keyInitializations():
    matrix, yaverty, vizov, qwerty, shtrafs, ant, skoropis, zubachew, diktor = massiveList()

    layouts = [
        Cortages(matrix, qwerty, 'йцукен'),
        Cortages(matrix, vizov, 'вызов'),
        Cortages(matrix, yaverty, 'яверты'),
        Cortages(matrix, shtrafs, 'ШТРАФЫ'),
        Cortages(matrix, ant, 'ант'),
        Cortages(matrix, skoropis, 'скоропись'),
        Cortages(matrix, zubachew, 'зубачев'),
        Cortages(matrix, diktor, 'диктор')
    ]


    # Асинхронно создаём кортежи и обрабатываем символы
    await asyncio.gather(*(layout.initialize() for layout in layouts))


    return {
        layout.layout_name: {
            'name': layout.layout_name,
            'bukvaKey': layout.bukvaKey,
            'fingerKey': layout.fingerKey,
            'shtrafKey': layout.shtrafKey,
            'fingerShtraf': layout.fingerShtraf,
            'modifierMap': layout.modifierMap,
            '_sym_to_finger': layout.sym_to_finger
        }
        for layout in layouts
    }


async def importFromFiles(textFile, digramsFile, csvFile):
    async with aiofiles.open(textFile, "r", encoding="utf-8") as f:
        text = await f.read()

    async with aiofiles.open(digramsFile, "r", encoding="utf-8") as f:
        lines = await f.readlines()
        digrams = [line.strip() for line in lines]

    csvText = pd.read_csv(csvFile, header=None, sep=",")

    return text, digrams, csvText
