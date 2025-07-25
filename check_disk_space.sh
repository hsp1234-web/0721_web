#!/bin/bash
# 腳本：check_disk_space.sh
# 功能：檢查並顯示當前檔案系統的磁碟空間使用情況。

echo "=== 開始檢查磁碟空間 ==="
df -h
echo "=== 磁碟空間檢查完畢 ==="
