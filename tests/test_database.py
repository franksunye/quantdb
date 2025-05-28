# tests/test_database.py

import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch

from src.api.database import initialize_database, insert_asset

class TestDatabase(unittest.TestCase):

    def setUp(self):
        # Create a temporary database file for testing
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()

        # Patch the DATABASE_PATH to use our temporary file
        self.patcher = patch('src.database.DATABASE_PATH', self.temp_db_path)
        self.mock_db_path = self.patcher.start()

        # Initialize the database
        initialize_database()

    def tearDown(self):
        # Stop the patcher
        self.patcher.stop()

        # Remove the temporary database file
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_insert_asset(self):
        # Connect to the temporary database
        conn = sqlite3.connect(self.temp_db_path)

        # Insert an asset
        insert_asset(conn, '600519', '贵州茅台', 'CNE0000018R8', 'stock', 'SHSE', 'CNY')

        # Verify the asset was inserted
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assets WHERE symbol = '600519'")
        asset = cursor.fetchone()
        self.assertIsNotNone(asset)
        self.assertEqual(asset[1], '600519')
        conn.close()

if __name__ == '__main__':
    unittest.main()
