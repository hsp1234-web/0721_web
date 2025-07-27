# -*- coding: utf-8 -*-
"""
伺服器模組 (APIServer)

負責啟動和管理 Web 伺服器，處理 API 請求。
這裡我們可以使用一個輕量級的框架，例如 Flask 或 FastAPI。
為了簡單起見，我們先定義一個基本的伺服器結構。
"""

from flask import Flask, jsonify
from .utils.error_handler import handle_api_error
from .environment import EnvironmentError

class APIServer:
    """
    API 伺服器類別。
    """
    def __init__(self, config, env_checker):
        self.app = Flask(__name__)
        self.config = config
        self.env_checker = env_checker
        self._register_routes()
        self._register_error_handlers()

    def _register_routes(self):
        """
        註冊 API 路由。
        """
        @self.app.route("/")
        def index():
            return "伺服器運行中！"

        @self.app.route("/health")
        def health_check():
            """
            提供一個健康檢查的端點。
            """
            try:
                # 在健康檢查時，也做一次環境檢查
                self.env_checker.run_all_checks()
                return jsonify({"status": "ok", "message": "系統資源正常"}), 200
            except EnvironmentError as e:
                return jsonify({"status": "error", "message": str(e)}), 503 # Service Unavailable

        # 業務邏輯路由可以集中在一個函式中註冊
        self._register_business_routes()

    def _register_business_routes(self):
        """
        註冊所有業務邏輯相關的路由。
        當業務邏輯變多時，可以將這個函式拆分到不同的模組。
        """
        from .logic import transcription_logic

        self.app.add_url_rule(
            '/upload',
            view_func=transcription_logic.upload_and_transcribe,
            methods=['POST']
        )
        self.app.add_url_rule(
            '/status/<task_id>',
            view_func=transcription_logic.get_task_status,
            methods=['GET']
        )

        # -- 金融分析相關路由 --
        from .logic import financial_analysis_logic
        self.app.add_url_rule(
            '/analysis/build',
            view_func=financial_analysis_logic.start_feature_store_build,
            methods=['POST']
        )

    def _register_error_handlers(self):
        """
        註冊統一的錯誤處理器。
        """
        self.app.register_error_handler(Exception, handle_api_error)


    def run(self):
        """
        啟動伺服器。
        """
        self.app.run(host=self.config.HOST, port=self.config.PORT)
