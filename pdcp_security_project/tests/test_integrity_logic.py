# C:\Users\sushma\Downloads\alldownloadnotes\5g_tech\codes\pdcp_security_project\tests\test_integrity_logic.py
import unittest
import sys

print("sys.path inside test_integrity_logic.py:")
for p in sys.path:
    print(f"  - {p}")

class TestMinimal(unittest.TestCase):
    def test_simple_truth(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()