#!/bin/bash
# 腳本：pre-install-check.sh - 智慧型套件大小檢查器

THRESHOLD_MB=100
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo "用法: $0 <package_name_1> [package_name_2] ..."
    exit 1
fi

echo "正在預估套件大小: $@"
# 建立一個臨時報告檔案
REPORT_FILE=$(mktemp)

# 模擬安裝並產生報告
poetry run pip install --dry-run --report "$REPORT_FILE" "$@" > /dev/null 2>&1

# 計算總大小
TOTAL_SIZE_BYTES=$(jq -r '[.install[] | .download_info.archive_info.size] | add' "$REPORT_FILE")
TOTAL_SIZE_MB=$((TOTAL_SIZE_BYTES / 1024 / 1024))

echo "預計總下載大小: ${TOTAL_SIZE_MB} MB"

# 檢查是否超過閾值
if (( TOTAL_SIZE_MB > THRESHOLD_MB )); then
    echo -e "${RED}警告：預計下載大小 (${TOTAL_SIZE_MB} MB) 超過 ${THRESHOLD_MB} MB 的閾值！${NC}"
    read -p "您確定要繼續安裝嗎？(y/N): " choice
    case "$choice" in
      y|Y )
        echo "使用者同意繼續，正在安裝..."
        poetry add "$@"
        ;;
      * )
        echo "安裝已取消。"
        exit 1
        ;;
    esac
else
    echo "套件大小在可接受範圍內，正在安裝..."
    poetry add "$@"
fi

# 清理臨時檔案
rm "$REPORT_FILE"
