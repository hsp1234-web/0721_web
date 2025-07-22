import sys
print("--- Python Executable ---")
print(sys.executable)
print("\n--- sys.path ---")
for path in sys.path:
    print(path)
print("\n--- Attempting to import critical packages ---")

try:
    import torch
    print("[SUCCESS] Imported torch")
    print(f"  - Version: {torch.__version__}")
    print(f"  - Path: {torch.__file__}")
except ImportError as e:
    print(f"[FAILED] Could not import torch: {e}")
    sys.exit(1)

try:
    import whisper
    print("[SUCCESS] Imported whisper")
    print(f"  - Path: {whisper.__file__}")
except ImportError as e:
    print(f"[FAILED] Could not import whisper: {e}")
    sys.exit(1)

try:
    import uvicorn
    print("[SUCCESS] Imported uvicorn")
    print(f"  - Version: {uvicorn.__version__}")
    print(f"  - Path: {uvicorn.__file__}")
except ImportError as e:
    print(f"[FAILED] Could not import uvicorn: {e}")
    sys.exit(1)

print("\n--- All critical packages imported successfully ---")
sys.exit(0)
