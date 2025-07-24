# 檔案: IPython/display.py
# 說明: 這是 IPython.display 模組的模擬版本，用於本地測試。

def display(*args, **kwargs):
    """模擬的 display 函式。在測試中我們不需要實際顯示任何東西。"""
    # print(f"DUMMY: display({args}, {kwargs})")
    pass

def update_display(*args, **kwargs):
    """模擬的 update_display 函式。在測試中我們不需要實際更新任何東西。"""
    # print(f"DUMMY: update_display({args}, {kwargs})")
    pass

def HTML(html_string):
    """模擬的 HTML 類別。只需要存在即可。"""
    return f"DUMMY_HTML({html_string[:30]}...)"
