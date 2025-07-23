# 鳳凰之心計畫：智慧安裝器
#
# 這個腳本將取代標準的 `poetry install`，成為一個能夠主動感知系統資源、
# 預測風險並做出智慧決策的安裝管理器。

import psutil
import subprocess
import requests

# --- 常數定義 ---
SAFETY_THRESHOLD_GB = 3.0
LARGE_PACKAGE_THRESHOLD_MB = 50.0

def get_available_space_gb():
    """獲取根目錄的可用空間，並轉換為 GB。"""
    disk_usage = psutil.disk_usage('/')
    return disk_usage.free / (1024**3)

def get_package_size_mb(package_name):
    """查詢給定套件的發行版大小。"""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status()
        data = response.json()
        releases = data.get("releases", {})
        if not releases:
            return 0
        latest_version = max(releases.keys())
        for file_info in releases[latest_version]:
            if file_info.get("packagetype") == "bdist_wheel":
                return file_info.get("size", 0) / (1024 * 1024)
        return 0
    except requests.exceptions.RequestException as e:
        print(f"查詢套件 {package_name} 大小時出錯: {e}")
        return 0

import toml

def classify_dependencies():
    """將依賴項分為小型和大型套件。"""
    small_packages = []
    large_packages = []
    try:
        with open("pyproject.toml", "r") as f:
            data = toml.load(f)
        dependencies = data.get("project", {}).get("dependencies", [])
        for dep in dependencies:
            package_name = dep.split(" ")[0]
            size_mb = get_package_size_mb(package_name)
            if size_mb > LARGE_PACKAGE_THRESHOLD_MB:
                large_packages.append(package_name)
            else:
                small_packages.append(package_name)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        print(f"讀取 pyproject.toml 時出錯: {e}")
    return small_packages, large_packages

def execute_intelligent_install(small_packages, large_packages):
    """實現智慧安裝的核心邏輯。"""
    skipped_packages = []
    installed_packages = []

    # 1. 優先安裝小型套件
    print("--- 正在安裝小型基礎套件 ---")
    try:
        subprocess.run(["poetry", "add"] + small_packages, check=True)
        installed_packages.extend(small_packages)
    except subprocess.CalledProcessError as e:
        print(f"安裝小型套件時出錯: {e}")

    # 2. 逐一評估並安裝大型套件
    print("--- 正在評估大型套件 ---")
    for pkg in large_packages:
        available_space = get_available_space_gb()
        pkg_size_gb = get_package_size_mb(pkg) / 1024

        if (available_space - pkg_size_gb) > SAFETY_THRESHOLD_GB:
            print(f"✅ 空間充足，正在安裝 {pkg}...")
            try:
                subprocess.run(["poetry", "add", pkg], check=True)
                installed_packages.append(pkg)
            except subprocess.CalledProcessError as e:
                print(f"安裝大型套件 {pkg} 時出錯: {e}")
        else:
            print(f"⚠️ [空間預警] 硬碟空間不足，無法安裝大型套件 '{pkg}'。將略過此套件。")
            skipped_packages.append(pkg)

    return installed_packages, skipped_packages

def generate_summary_report(installed, skipped):
    """生成最終報告"""
    print("\n====================")
    print("📦 安裝總結報告")
    print("====================")
    print(f"✅ 成功安裝套件數量: {len(installed)}")
    if skipped:
        print(f"⚠️ 因空間不足而略過的套件數量: {len(skipped)}")
        for pkg in skipped:
            print(f"  - {pkg}")
    print("====================")

def main():
    """主執行流程"""
    available_space = get_available_space_gb()
    print(f"目前可用硬碟空間: {available_space:.2f} GB")

    small_packages, large_packages = classify_dependencies()
    print(f"小型套件: {small_packages}")
    print(f"大型套件: {large_packages}")

    installed, skipped = execute_intelligent_install(small_packages, large_packages)
    generate_summary_report(installed, skipped)

if __name__ == "__main__":
    main()
