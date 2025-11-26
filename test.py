"""
Модуль для тестирования приложения анализа раскладок.
Проверяет корректность инициализации раскладок, работу анализа текста
и формирование результатов.
"""
import pytest
import asyncio

# --- keyboardInit ---
from keyboardInit import keyInitializations

@pytest.mark.asyncio
async def test_all_layouts_present():
    """
    Проверяет, что keyInitializations возвращает все 7 раскладок.
    """
    layouts = await keyInitializations()
    expected = {"йцукен", "вызов", "диктор", "яверты", "ант", "зубачев", "скоропись"}
    assert expected.issubset(set(layouts.keys()))

@pytest.mark.asyncio
async def test_layouts_have_finger_keys():
    """
    Проверяет, что у каждой раскладки есть карта fingerKey.
    """
    layouts = await keyInitializations()
    for name in ["йцукен", "вызов", "диктор", "яверты", "ант", "зубачев", "скоропись"]:
        assert "fingerKey" in layouts[name]
        assert isinstance(layouts[name]["fingerKey"], dict)


# --- analyzation ---
from analization import TextAnalyzer

@pytest.mark.parametrize("layout_name", ["йцукен", "вызов", "диктор", "яверты", "ант", "зубачев", "скоропись"])
def test_base_index_shtraf_and_modifiers(layout_name):
    """
    Проверяет базовые штрафы и модификаторы для всех 7 раскладок.
    """
    analyzer = TextAnalyzer()
    analyzer.index_shtraf = {"A": 3}
    assert analyzer.base_index_shtraf("A") == 3
    assert analyzer.base_index_shtraf("X") == 0

    analyzer.explicit_shift_syms = {layout_name: {"ё"}}
    mod_info = {"shift": True}
    shtraf = analyzer.modifier_shtraf_for_symbol("А", layout_name, mod_info)
    assert shtraf == analyzer.shtraf_config["shift_penalty"]

    mod_info = {"alt": True, "ctrl": True}
    shtraf = analyzer.modifier_shtraf_for_symbol("x", layout_name, mod_info)
    assert shtraf == analyzer.shtraf_config["alt_penalty"] + analyzer.shtraf_config["ctrl_penalty"]


# --- Graphics ---
from Graphics import GraphicsAnalyzer

def test_graphics_has_all_layouts():
    """
    Проверяет, что GraphicsAnalyzer содержит все 7 раскладок
    с цветами и подписями.
    """
    layouts = {name: {"fingerKey": {}} for name in ["йцукен","вызов","диктор","яверты","ант","зубачев","скоропись"]}
    analyzer = GraphicsAnalyzer(layouts)

    expected = {"йцукен", "вызов", "диктор", "яверты", "ант", "зубачев", "скоропись"}
    assert expected.issubset(set(analyzer.layout_colors.keys()))
    assert expected.issubset(set(analyzer.layout_labels.keys()))

def test_graphics_prepare_results_adds_missing_fingers():
    """
    Проверяет, что GraphicsAnalyzer добавляет отсутствующие пальцы со значением 0.
    """
    layouts = {"йцукен": {"fingerKey": {"lfi1": [], "rfi1": []}}}
    analyzer = GraphicsAnalyzer(layouts)
    results = [["йцукен", 10, 2, 1, {"lfi1": 5}]]
    structured, all_data = analyzer._prepare_results(results)
    assert "rfi1" in structured[0]["finger_statistics"]
    assert structured[0]["finger_statistics"]["rfi1"] == 0


# --- CT ---
import CT

@pytest.mark.asyncio
async def test_ct_main_runs(monkeypatch):
    """
    Проверяет, что CT.main запускается без ошибок (с подменой анализа).
    """
    async def fake_run(self):
        return {"text": [["йцукен", 10, 1, 0, {"lfi1": 10}, {"left_only": 1, "right_only": 0, "both": 0}]]}
    CT.analization.TextAnalyzer.run_full_analysis = fake_run
    await CT.main()
