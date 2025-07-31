#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
依賴大小估算工具

本工具用於在不實際安裝的情況下，預估一個 `requirements.in` 檔案
所對應的完整依賴樹的總下載大小。

工作流程:
1. 使用 `pip-compile` 解析 `requirements.in` 以獲取完整的依賴列表。
2. 平行查詢 PyPI 的 JSON API 來獲取每個套件的元數據。
3. 從元數據中找到最適合當前平台的 Wheel 檔案。
4. 加總所有 Wheel 檔案的大小，得出最終預估值。
"""

import asyncio
import httpx
import subprocess
import sys
from pathlib import Path
import os

def get_resolved_dependencies(req_in_path: Path) -> list[str]:
    """
    使用 pip-compile 解析 requirements.in 檔案，並返回完整的依賴列表。
    This version uses a temporary file on disk to bypass stdout redirection issues.
    """
    if not req_in_path.exists():
        raise FileNotFoundError(f"找不到指定的 .in 檔案: {req_in_path}")

    print(f"📦 正在解析依賴檔案: {req_in_path}")

    output_file = Path("deps.tmp")
    compile_cmd = [
        sys.executable, "-m", "piptools", "compile",
        "--output-file", str(output_file),
        str(req_in_path)
    ]

    try:
        subprocess.run(compile_cmd, check=True, capture_output=True, text=True)

        if not output_file.exists():
            print("❌ pip-compile 成功執行，但未產生輸出檔。")
            return []

        content = output_file.read_text()

        packages = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # 處理行內註解並取得套件規格
            package_spec = line.split('#')[0].strip()
            if '==' in package_spec:
                packages.append(package_spec)
        print(f"✅ 解析完成，共發現 {len(packages)} 個依賴。")
        return packages

    except subprocess.CalledProcessError as e:
        print("❌ pip-compile 執行失敗:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        raise
    finally:
        # Clean up the temporary file
        if output_file.exists():
            output_file.unlink()


def get_wheel_size(metadata: dict, version: str) -> int:
    """
    從套件元數據中解析出指定版本的 Wheel 檔案大小。
    """
    if not metadata or "releases" not in metadata or version not in metadata["releases"]:
        return 0

    files = metadata["releases"][version]

    # 尋找最合適的 wheel 檔案
    # 優先順序: 1. py3-none-any (通用) 2. cp3-abi3 (穩定 ABI) 3. 任何 .whl
    best_wheel = None
    for f in files:
        if f.get("packagetype") == "bdist_wheel":
            if "py3-none-any" in f["filename"]:
                best_wheel = f
                break # 找到最佳的，直接跳出
            elif "cp3" in f["filename"] and "abi3" in f["filename"]:
                best_wheel = f # 備選
            elif best_wheel is None:
                best_wheel = f # 任何 wheel 都行

    if best_wheel:
        return best_wheel.get("size", 0)

    return 0 # 找不到 wheel

async def get_package_metadata(package_spec: str, client: httpx.AsyncClient) -> tuple[str, dict]:
    """
    從 PyPI 獲取單一套件的元數據，並返回套件規格和元數據。
    """
    package_name = package_spec.split('==')[0]
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = await client.get(url)
        response.raise_for_status()
        return package_spec, response.json()
    except httpx.HTTPStatusError as e:
        print(f"❌ 獲取 {package_name} 元數據失敗: {e}", file=sys.stderr)
        return package_spec, None


async def main():
    """主執行函數"""
    print("依賴大小估算工具啟動...")
    try:
        # 步驟 1: 解析依賴
        reqs_in_file = Path("apps/main_dashboard/requirements.in")
        dependencies = get_resolved_dependencies(reqs_in_file)

        # 步驟 2: 平行獲取所有套件的元數據
        print(f"\n🔎 正在從 PyPI 獲取 {len(dependencies)} 個套件的元數據...")
        async with httpx.AsyncClient() as client:
            tasks = [get_package_metadata(dep, client) for dep in dependencies]
            results = await asyncio.gather(*tasks)

        # 步驟 3: 計算總大小
        total_size = 0
        for spec, metadata in results:
            if metadata:
                version = spec.split('==')[1]
                size = get_wheel_size(metadata, version)
                total_size += size
                print(f"  - {spec:<30} ... {size/1024:.1f} KB")
            else:
                print(f"  - {spec:<30} ... 獲取失敗")

        print("\n" + "="*40)
        print(f"📦 預估總下載大小: {total_size / (1024*1024):.2f} MB")
        print("="*40)


    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"\n錯誤: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
