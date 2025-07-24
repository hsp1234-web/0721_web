# 檔案: google/colab/output.py
# 說明: 這是 google.colab.output 模組的模擬版本，用於本地測試。
#       它提供了一個 get_ τότε_output_url 函式的虛假實現，
#       以避免在非 Colab 環境中執行時出現 ImportError。

def get_ τότε_output_url(port, timeout_sec=20):
    """
    模擬的 get_ τότε_output_url 函式。
    在真實的 Colab 環境中，此函式會返回一個指向指定埠號的 URL。
    在測試環境中，我們只返回一個固定的假 URL。
    """
    # 為了讓測試穩定，我們不引入隨機性或超時。
    # 只要呼叫了這個函式，就假設埠號已經就緒。
    return f"http://localhost:{port}/mock_colab_url"

def display(*args, **kwargs):
    """模擬的 display 函式。在測試中我們不需要實際顯示任何東西。"""
    pass

def update_display(*args, **kwargs):
    """模擬的 update_display 函式。在測試中我們不需要實際更新任何東西。"""
    pass

def HTML(html_string):
    """模擬的 HTML 類別。只需要存在即可。"""
    return f"DUMMY_HTML({html_string[:30]}...)"
