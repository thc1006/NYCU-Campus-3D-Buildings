#!/bin/bash
# NQSD 數據整理工具 - Linux/Mac Shell 腳本
# 使用 Docker Compose 運行整理流程

set -e

echo "========================================"
echo "NQSD 數據整理工具"
echo "========================================"
echo ""

show_menu() {
    echo "請選擇操作:"
    echo "  1. 創建備份"
    echo "  2. 執行整理"
    echo "  3. 驗證結果"
    echo "  4. 完整流程（備份 + 整理 + 驗證）"
    echo "  5. 查看當前備份"
    echo "  0. 退出"
    echo ""
}

backup() {
    echo ""
    echo "[1/1] 創建備份..."
    docker-compose run --rm backup-creator
    echo ""
    echo "✅ 備份完成！"
}

organize() {
    echo ""
    echo "[1/1] 執行整理..."
    docker-compose run --rm data-organizer
    echo ""
    echo "✅ 整理完成！"
}

validate() {
    echo ""
    echo "[1/1] 驗證結果..."
    docker-compose run --rm data-validator
    echo ""
    echo "✅ 驗證完成！"
}

full_process() {
    echo ""
    echo "開始完整流程..."
    echo ""
    echo "[1/3] 創建備份..."
    docker-compose run --rm backup-creator
    echo ""
    echo "[2/3] 執行整理..."
    docker-compose run --rm data-organizer
    echo ""
    echo "[3/3] 驗證結果..."
    docker-compose run --rm data-validator
    echo ""
    echo "========================================"
    echo "✅ 完整流程執行完畢！"
    echo "========================================"
}

list_backups() {
    echo ""
    echo "當前備份列表:"
    ls -lh backup/backup_* 2>/dev/null || echo "  沒有找到備份"
    echo ""
}

while true; do
    show_menu
    read -p "請輸入選項 (0-5): " choice

    case $choice in
        1) backup ;;
        2) organize ;;
        3) validate ;;
        4) full_process ;;
        5) list_backups ;;
        0) echo ""; echo "再見！"; exit 0 ;;
        *) echo ""; echo "❌ 無效的選項！"; echo "" ;;
    esac

    echo ""
    read -p "按 Enter 鍵繼續..."
    clear
done
