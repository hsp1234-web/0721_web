import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

from launcher.src.core.environment import EnvironmentManager

@pytest.mark.unit
class TestEnvironmentManager(unittest.TestCase):

    def setUp(self):
        self.project_path = Path("/tmp/mock_project")
        self.manager = EnvironmentManager(self.project_path, min_disk_space_mb=100, max_memory_usage_percent=90)

    @patch('psutil.disk_usage')
    def test_check_disk_space_sufficient(self, mock_disk_usage):
        """測試磁碟空間充足的情況"""
        # 模擬返回 200 GB 可用空間
        mock_disk_usage.return_value = MagicMock(free=200 * 1024**3)
        self.assertTrue(self.manager.check_disk_space())

    @patch('psutil.disk_usage')
    def test_check_disk_space_insufficient(self, mock_disk_usage):
        """測試磁碟空間不足的情況"""
        # 模擬返回 50 MB 可用空間
        mock_disk_usage.return_value = MagicMock(free=50 * 1024**2)
        self.assertFalse(self.manager.check_disk_space())

    @patch('psutil.virtual_memory')
    def test_check_memory_sufficient(self, mock_virtual_memory):
        """測試記憶體使用率正常的情況"""
        # 模擬返回 50% 的使用率
        mock_virtual_memory.return_value = MagicMock(percent=50)
        self.assertTrue(self.manager.check_memory())

    @patch('psutil.virtual_memory')
    def test_check_memory_insufficient(self, mock_virtual_memory):
        """測試記憶體使用率過高的情況"""
        # 模擬返回 95% 的使用率
        mock_virtual_memory.return_value = MagicMock(percent=95)
        self.assertFalse(self.manager.check_memory())

if __name__ == '__main__':
    unittest.main()
