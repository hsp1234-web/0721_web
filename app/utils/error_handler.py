# -*- coding: utf-8 -*-
"""
統一錯誤處理模組 (ErrorHandler)
"""
from flask import jsonify
import logging

# 假設我們有一個日誌記錄器
logger = logging.getLogger(__name__)

def handle_api_error(error):
    """
    一個通用的 API 錯誤處理器。
    它會捕捉所有未處理的例外，記錄它們，並回傳一個標準的 JSON 錯誤訊息。
    """
    # 在真實世界中，你可能會想區分不同類型的錯誤，
    # 例如，對於已知的錯誤（如驗證錯誤）回傳 400，
    # 對於未知的伺服器內部錯誤回傳 500。

    # 記錄錯誤的詳細資訊，方便排查問題
    logger.exception(f"發生未預期的錯誤: {error}")

    response = {
        "status": "error",
        "message": "伺服器發生內部錯誤，我們已經記錄下來並會盡快處理。"
    }

    # 根據錯誤類型可以自訂回傳的狀態碼和訊息
    # if isinstance(error, ValueError):
    #     response["message"] = "輸入的資料格式不正確。"
    #     return jsonify(response), 400

    return jsonify(response), 500
