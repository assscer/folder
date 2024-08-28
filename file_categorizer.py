import os
import logging
from typing import Dict, List, Optional
import unittest
from pathlib import Path
import tempfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class InvalidDirectoryError(Exception):
    pass


def is_file_valid(file_path: str, min_size: Optional[int], max_size: Optional[int],
                  modified_after: Optional[float], modified_before: Optional[float]) -> bool:
    try:
        file_stats = os.stat(file_path)
    except OSError:
        logging.warning("Не удалось получить информацию о файле: %s", file_path)
        return False

    if min_size is not None and file_stats.st_size < min_size:
        return False
    if max_size is not None and file_stats.st_size > max_size:
        return False
    if modified_after is not None and file_stats.st_mtime < modified_after:
        return False
    if modified_before is not None and file_stats.st_mtime > modified_before:
        return False

    return True


def categorize_files_by_type(folder_path: str, min_size: Optional[int] = None, max_size: Optional[int] = None,
                             modified_after: Optional[float] = None, modified_before: Optional[float] = None) -> Dict[str, List[str]]:
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        logging.error("Указанный путь не существует или не является папкой: %s", folder_path)
        raise InvalidDirectoryError(f"Указанный путь не существует или не является папкой: {folder_path}")

    file_type_dict = {}

    for root, _, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1] or ''

            if not is_file_valid(full_path, min_size, max_size, modified_after, modified_before):
                continue

            file_type_dict.setdefault(file_extension, []).append(full_path)
            logging.info("Файл добавлен: %s", full_path)

    return file_type_dict


class TestCategorizeFilesByType(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        Path(self.test_dir.name, 'file1.txt').write_text('sample text')
        Path(self.test_dir.name, 'file2.jpg').write_text('sample image')
        Path(self.test_dir.name, 'subfolder').mkdir()
        Path(self.test_dir.name, 'subfolder', 'file3.pdf').write_text('sample pdf')

    def tearDown(self):
        self.test_dir.cleanup()

    def test_categorize_files_by_type(self):
        result = categorize_files_by_type(self.test_dir.name)
        self.assertIn('.txt', result)
        self.assertIn('.jpg', result)
        self.assertIn('.pdf', result)
        self.assertEqual(len(result['.txt']), 1)
        self.assertEqual(len(result['.jpg']), 1)
        self.assertEqual(len(result['.pdf']), 1)

    def test_empty_folder(self):
        empty_dir = tempfile.TemporaryDirectory()
        result = categorize_files_by_type(empty_dir.name)
        self.assertEqual(result, {})
        empty_dir.cleanup()

    def test_invalid_path(self):
        with self.assertRaises(InvalidDirectoryError):
            categorize_files_by_type('/test/path')


if __name__ == "__main__":
    unittest.main()
