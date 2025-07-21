from src.archiver import generate_final_log_file
from pathlib import Path

DB_PATH = Path("logs.sqlite")
OUTPUT_DIR = Path("logs")

generate_final_log_file(DB_PATH, OUTPUT_DIR)
