def get_colab_url(port, timeout_sec=20, **kwargs): return f"http://mock-colab-url-for-port-{port}"
def display(*args, **kwargs): print(f"MockDisplay: {args}")
def update_display(*args, **kwargs): print(f"MockUpdateDisplay: {args}")
def HTML(s): return f"HTML_CONTENT: {s}"
