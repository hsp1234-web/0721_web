# -*- coding: utf-8 -*-
"""
共用工具模組

這個目錄包含一些可以在整個應用程式中重複使用的工具，
例如日誌記錄器、錯誤處理器等。
"""
from .logger import get_logger
from .error_handler import handle_api_error
