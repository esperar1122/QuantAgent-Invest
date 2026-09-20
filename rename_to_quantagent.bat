@echo off
chcp 65001 >nul
echo ========================================================
echo  QuantAgent-Invest 离线物理目录更名脚本
echo ========================================================
echo.
echo 注意：请确保已关闭当前运行的 IDE (如 Antigravity / VS Code) 
echo 以及所有后台运行的 Python 和 Node.js 进程！
echo.
pause

set "PARENT_DIR=%~dp0.."
set "OLD_DIR=%~dp0"
set "NEW_DIR=%PARENT_DIR%\QuantAgent-Invest"

echo.
echo 正在检查是否已存在目录联接并清理...
if exist "%NEW_DIR%" (
    rmdir "%NEW_DIR%" 2>nul
)

echo.
echo 正在执行目录更名:
echo %OLD_DIR% -> %NEW_DIR%
echo.

cd /d "%PARENT_DIR%"
ren "%OLD_DIR:~0,-1%" "QuantAgent-Invest"

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo  更名成功！请使用 IDE 直接打开:
    echo  E:\Project\QuantAgent-Invest
    echo ========================================================
) else (
    echo.
    echo [错误] 更名失败，可能有进程仍在占用此文件夹。
    echo 请在任务管理器中关闭 node.exe / python.exe 后重试。
)
echo.
pause
