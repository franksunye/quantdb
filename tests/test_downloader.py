# tests/test_downloader.py

import unittest
from src.downloader import download_index_data

class TestDownloader(unittest.TestCase):

    def test_download_index_data(self):
        data = download_index_data("000688")
        self.assertIsNotNone(data)
        self.assertGreater(len(data), 0)

if __name__ == '__main__':
    unittest.main()
