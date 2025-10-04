import asyncio
import aiofiles
import pandas as pd

class CreatorBase: # Класс, разделяющий клавиши на правую и левую руку
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
        # матрица с кодами клавиш
        self.matrix = matrix #индексы
        self.symbols = symbols  # одна конкретная раскладка
        self.layout_name = layout_name

        self.fingerKey = {} # палец - индекс
        self.bukvaKey = {} # буква - индекс
        self.bukvaFinger = {} #буква - палец
        self.shtrafKey = {} # штраф - ключ
        self.fingerShtraf = {} # палец - штраф




    async def create_tuples(self): #палец - индекс
        left, right = self.split()
        abj_left = left.copy()
        abj_left[0] = abj_left[0][1:]
        self.fingerKey["lfi5"] = ('41', '02', '16', '30', '44')
        self.fingerKey["lfi4"] = tuple(row[1] for row in abj_left)
        self.fingerKey["lfi3"] = tuple(row[2] for row in abj_left)
        self.fingerKey["lfi2"] = tuple(row[i] for row in abj_left for i in (3, 4))

        self.fingerKey["rfi2"] = tuple(row[i] for row in right for i in (3, 4))
        self.fingerKey["rfi3"] = tuple(row[2] for row in right)
        self.fingerKey["rfi4"] = tuple(row[3] for row in right)
        self.fingerKey["rfi5"] = ('11', '12', '13', '25', '26', '27', '43', '39', '40', '53')

        self.fingerKey["lfi1"] = ('SHIFT42', 'ALT56')

        await asyncio.sleep(0)

    async def process_bukva_index(self):
        self.modifierMap = {}  # символ → {'shift': bool, 'alt': bool}

        for row_idx, row in enumerate(self.symbols):
            pointer = 0  # указывает на колонку в self.matrix[row_idx]
            last_key = None  # индекс последней «обычной» клавиши

            for tok in row:
                if pointer >= len(self.matrix[row_idx]):
                    break

                idx = self.matrix[row_idx][pointer]

                # 1) обычный символ (без shift/alt)
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

                # 2) shift-модификатор
                if tok.startswith('shift+'):
                    sym = tok.split('+', 1)[1]
                    self.bukvaKey.setdefault(last_key, [])
                    if sym not in self.bukvaKey[last_key]:
                        self.bukvaKey[last_key].append(sym)
                        self.modifierMap[sym] = {'shift': True, 'alt': False}
                    continue

                # 3) alt-модификатор
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

        self.sym_to_finger = {}
        for finger, key_ids in self.fingerKey.items():
            for key_id in key_ids:
                for sym in self.bukvaKey.get(key_id, []):
                    self.sym_to_finger[sym] = finger


def massiveList():
    matrix = [['41', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'],
              ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '43'],
              ['30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40'],
              ['44', '45', '46', '47', '48', '49', '50', '51', '52', '53']]

    yaverty = [['ю', '1', 'shift+!', '2', 'shift+@', '3', 'shift+ё', '4', 'shift+Ё', '5', 'shift+ъ',
                '6', 'shift+ъ', '7', 'shift+&', '8', 'shift+*', '9', 'shift+(', '0', 'shift+)', '-', 'shift+_', 'ч'],
               ['я', 'в', 'е', 'р', 'т', 'ы', 'у', 'и', 'о', 'п', 'ш', 'щ', 'э'],
               ['а', 'с', 'д', 'ф', 'г', 'х', 'й', 'к', 'л', ';', 'shift+:', '--', 'shift+"'],
               ['з', 'ь', 'ц', 'ж', 'б', 'н', 'м', ',', 'shift+<', '.', 'shift+>', '/', 'shift+?']]

    vizov = [['ю', 'ё', '7', 'shift+[', '5', 'shift+{', '3', 'shift+}', '1', 'shift+(', '9', 'shift+=', '0',
              'shift+*', '2', 'shift+)', '4', 'shift++', '6', 'shift+]', '8', 'shift+!', 'щ'],
             ['б', 'ы', 'о', 'у', 'alt+ю', 'ь', 'ё', 'л', 'д', 'я', 'г', 'ж', 'ц'],
             ['ъ', 'ч', 'alt+ц', 'и', 'е', 'alt+э', 'а', ',', 'shift+;', '.', 'shift+:', 'н', 'alt+щ'],
             ['т', 'alt+ъ', 'с', 'в', 'з', 'ш', 'х', 'й', 'к', '_', 'shift+-', 'э', 'р']]

    qwerty = [['ё', '1', 'shift+!', '2', 'shift+"', '3', 'shift+№', '4', 'shift+;', '5', 'shift+%', '6', 'shift+:', '7',
               'shift+?', '8', 'shift+*', '9', 'shift+(', '0', 'shift+)', '-', 'shift+_', '=', 'shift++'],
              ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ'],
              ['ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э'],
              ['я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю', '.']]

    shtrafs = [['6', '5', '4', '4', '4', '4', '4', '4', '4', '4', '4', '5', '6'],
              ['3', '2', '2', '2', '2', '2', '2', '2', '2', '2', '3', '5', '6'],
              ['0', '0', '0', '0', '1', '1', '0', '0', '0', '0', '1'],
              ['2', '2', '2', '2', '3', '3', '2', '2', '2', '2']]

    return matrix, yaverty, vizov, qwerty, shtrafs

async def debugingFunction(layouts):
    for layout in layouts:
        print(f"\n📋 Раскладка: {layout.layout_name}")
        for keyIndex in sorted(layout.bukvaKey.keys(), key=lambda x: int(x)):
            joined = " | ".join(layout.bukvaKey[keyIndex])
            print(f"Клавиша {keyIndex}: {joined}")
        for k, v in layout["_sym_to_finger"].items():
            if v == "rfi2":
                print(k)


async def keyInitializations():
    matrix, yaverty, vizov, qwerty, shtrafs = massiveList()

    layouts = [
        Cortages(matrix, qwerty, 'qwerty'),
        Cortages(matrix, vizov, 'vizov'),
        Cortages(matrix, yaverty, 'yaverty'),
        Cortages(matrix, shtrafs, 'ШТРАФЫ')
    ]

    # Асинхронно создаём кортежи и обрабатываем символы
    await asyncio.gather(*(layout.initialize() for layout in layouts))

    # Выводим результат
    #await debugingFunction(layouts)



    return {
        layout.layout_name: {
            'name' : layout.layout_name,
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
