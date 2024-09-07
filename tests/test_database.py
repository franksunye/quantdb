# tests/test_database.py

import unittest
from src.database import initialize_database, insert_asset
import sqlite3
from src.config import DATABASE_PATH

class TestDatabase(unittest.TestCase):

    def setUp(self):
        initialize_database()

    def test_insert_asset(self):
        insert_asset('600519', '贵州茅台', 'CNE0000018R8', 'stock', 'SHSE', 'CNY')
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ASSETS WHERE symbol = '600519'")
        asset = cursor.fetchone()
        self.assertIsNotNone(asset)
        self.assertEqual(asset[1], '600519')
        conn.close()

if __name__ == '__main__':
    unittest.main()
