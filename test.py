"""
Модуль для тестирования приложения анализа раскладок.
Проверяет корректность инициализации раскладок, работу анализа текста
и формирование результатов.
"""

import asyncio
import unittest
from analization import TextAnalyzer
from keyboardInit import keyInitializations


class KeyboardLayoutsTest(unittest.TestCase):

    def setUp(self):
        # Инициализация раскладок
        self.layouts = asyncio.run(keyInitializations())
        self.analyzer = TextAnalyzer(debug_mode=True)
        self.analyzer.layouts = self.layouts

    def test_layouts_exist(self):
        """Проверяем, что все раскладки загружены"""
        self.assertIn("qwerty", self.layouts)
        self.assertIn("vizov", self.layouts)
        self.assertIn("yaverty", self.layouts)
        self.assertIn("ШТРАФЫ", self.layouts)

    def test_symbol_resolution(self):
        """Проверяем, что символы корректно мапятся на пальцы"""
        result = self.analyzer.resolve_symbol("а", "yaverty")
        self.assertIsNotNone(result)
        idx, mod_info, finger = result
        self.assertTrue(finger.startswith("lfi") or finger.startswith("rfi"))

    def test_compare_layouts(self):
        """Проверяем анализ короткого текста"""
        text = "Привет мир"
        results = asyncio.run(self.analyzer.compareLayouts(text, self.layouts))
        structured = self.analyzer.returnResults(results)
        self.assertGreater(len(structured), 0)
        for layout in structured:
            self.assertIn("total_load", layout)
            self.assertIn("finger_statistics", layout)


if __name__ == "__main__":
    unittest.main()
