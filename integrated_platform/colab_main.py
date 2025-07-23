from pathlib import Path
from integrated_platform.src.colab.colab_manager import ColabManager

if __name__ == "__main__":
    LOG_DB_PATH = Path("logs.sqlite")
    colab_manager = ColabManager(LOG_DB_PATH)

    colab_manager.start()

    colab_manager.run_shell_command("bash run.sh")
    colab_manager.create_public_portal()

    colab_manager.stop()
