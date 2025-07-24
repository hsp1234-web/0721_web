import shutil
import sys
import tomllib
from pathlib import Path

# --- 常數定義 ---
# 安全閾值（以 GB 為單位）
# 如果可用空間低於此值，將觸發嚴格模式
DISK_STRICT_THRESHOLD_GB = 3.0
# 如果預測安裝後剩餘空間低於此值，則拒絕安裝大型套件
DISK_MIN_REMAINING_GB = 1.5

# 預估大型套件的安裝後大小（以 GB 為單位）
# 這是一個簡化的估算，實際大小可能因版本和依賴而異
ESTIMATED_SIZES_GB = {
    "full": 5.0, # 假設 "full" extra 群組總共需要 5GB
    # 可以為其他 extras 群組添加更多估算
    # "another-extra": 2.0,
}

# --- 輔助函式 ---
def get_disk_usage():
    """獲取磁碟總空間、已用空間和可用空間（以 GB 為單位）。"""
    total, used, free = shutil.disk_usage("/")
    total_gb = total / (1024**3)
    used_gb = used / (1024**3)
    free_gb = free / (1024**3)
    return total_gb, used_gb, free_gb

def print_colored(text, color_code, file=sys.stderr):
    """在終端輸出帶有顏色的文字。"""
    print(f"\033[{color_code}m{text}\033[0m", file=file)

def print_report(free_gb, requested_extras):
    """打印資源報告和安裝決策。"""
    print_colored("--- 資源評估與安裝決策報告 ---", "1;34")
    print_colored(f"可用磁碟空間: {free_gb:.2f} GB", "1;34")

    if not requested_extras:
        print_colored("未請求安裝任何大型套件組 (extras)。", "32")
        return

    print_colored(f"請求安裝的大型套件組: {', '.join(requested_extras)}", "34")

    for extra in requested_extras:
        estimated_size = ESTIMATED_SIZES_GB.get(extra, 0)
        predicted_free_gb = free_gb - estimated_size

        print_colored(f"\n分析套件組 '{extra}':", "1;33")
        print_colored(f"  - 預估需要空間: {estimated_size:.2f} GB", "33")
        print_colored(f"  - 預測安裝後剩餘空間: {predicted_free_gb:.2f} GB", "33")

        if free_gb < DISK_STRICT_THRESHOLD_GB:
            print_colored(f"  - [警告] 目前可用空間 ({free_gb:.2f}GB) 低於嚴格模式閾值 ({DISK_STRICT_THRESHOLD_GB}GB)。", "33")

        if predicted_free_gb < DISK_MIN_REMAINING_GB:
            print_colored(f"  - [決策] 跳過 '{extra}'。預測剩餘空間低於安全下限 ({DISK_MIN_REMAINING_GB}GB)。", "1;31")
        else:
            print_colored(f"  - [決策] 同意安裝 '{extra}'。資源充足。", "32")

# --- 主要邏輯 ---
def main():
    """
    智慧依賴管理器的主要進入點。
    返回一個適合 `poetry install` 的命令字串。
    """
    try:
        with open("pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
        all_extras = pyproject.get("tool", {}).get("poetry", {}).get("extras", {})
    except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
        print_colored(f"[錯誤] 無法讀取或解析 pyproject.toml: {e}", "1;31")
        return "poetry install --no-root" # 返回一個安全的預設值

    requested_extras = list(all_extras.keys())

    _, _, free_gb = get_disk_usage()

    print_report(free_gb, requested_extras)

    installable_extras = []
    for extra in requested_extras:
        estimated_size = ESTIMATED_SIZES_GB.get(extra, 0)
        predicted_free_gb = free_gb - estimated_size

        if predicted_free_gb >= DISK_MIN_REMAINING_GB:
            installable_extras.append(extra)

    # 構建最終的 poetry install 命令
    command = "poetry install --no-root"
    if installable_extras:
        # 對於 extras，正確的語法是 -E <extra_name>
        # 我們可以一次性安裝所有可安裝的 extras
        extras_string = " ".join([f"-E {extra}" for extra in installable_extras])
        command += f" {extras_string}"

    print_colored("\n" + "="*40, "1;36")
    print_colored(f"最終執行的安裝指令: {command}", "1;36")
    print_colored("="*40 + "\n", "1;36")

    return command

if __name__ == "__main__":
    final_command = main()
    # 將最終指令輸出到標準輸出，以便 run.sh 捕獲和執行
    print(final_command)
