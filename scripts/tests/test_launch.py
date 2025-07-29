import subprocess
import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scripts.launch import check_service_health, AppPreparationError, prepare_app_environment


def test_check_service_health_success():
    """測試服務成功啟動時的健康檢查"""
    with patch("httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        assert check_service_health("test_app", 8000, timeout=5) is True


def test_check_service_health_timeout():
    """測試服務啟動超時的健康檢查"""
    with patch("httpx.get", side_effect=httpx.RequestError("Connection failed")):
        assert check_service_health("test_app", 8000, timeout=2) is False


def test_check_service_health_retry_and_succeed():
    """測試服務在重試後成功啟動的健康檢查"""
    with patch("httpx.get") as mock_get:
        mock_get.side_effect = [
            httpx.RequestError("Connection failed"),
            MagicMock(status_code=200),
        ]
        assert check_service_health("test_app", 8000, timeout=5) is True
        assert mock_get.call_count == 2
