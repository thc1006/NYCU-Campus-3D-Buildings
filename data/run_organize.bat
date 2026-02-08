@echo off
REM NQSD 數據整理工具 - Windows 批次腳本
REM 使用 Docker Compose 運行整理流程

echo ========================================
echo NQSD 數據整理工具
echo ========================================
echo.

echo 請選擇操作:
echo   1. 創建備份
echo   2. 執行整理
echo   3. 驗證結果
echo   4. 完整流程（備份 + 整理 + 驗證）
echo   5. 查看當前備份
echo   0. 退出
echo.

set /p choice=請輸入選項 (0-5):

if "%choice%"=="1" goto backup
if "%choice%"=="2" goto organize
if "%choice%"=="3" goto validate
if "%choice%"=="4" goto full
if "%choice%"=="5" goto list_backups
if "%choice%"=="0" goto end

echo 無效的選項！
pause
exit /b

:backup
echo.
echo [1/1] 創建備份...
docker-compose run --rm backup-creator
echo.
echo 備份完成！
pause
exit /b

:organize
echo.
echo [1/1] 執行整理...
docker-compose run --rm data-organizer
echo.
echo 整理完成！
pause
exit /b

:validate
echo.
echo [1/1] 驗證結果...
docker-compose run --rm data-validator
echo.
echo 驗證完成！
pause
exit /b

:full
echo.
echo 開始完整流程...
echo.
echo [1/3] 創建備份...
docker-compose run --rm backup-creator
echo.
echo [2/3] 執行整理...
docker-compose run --rm data-organizer
echo.
echo [3/3] 驗證結果...
docker-compose run --rm data-validator
echo.
echo ========================================
echo 完整流程執行完畢！
echo ========================================
pause
exit /b

:list_backups
echo.
echo 當前備份列表:
dir /b backup\backup_*
echo.
pause
exit /b

:end
echo.
echo 再見！
exit /b
