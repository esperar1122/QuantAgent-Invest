# QuantAgent-Invest Development Startup Script
# 智能投研系统一键开发启动脚本

[CmdletBinding(PositionalBinding=$false)]
param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$WithWorker,
    [switch]$WorkerOnly,
    [int]$Port = 8000,
    [int]$WorkerPort = 8001,
    [switch]$Help,
    [switch]$NoReload,
    # 兼容统一命令行参数: start_dev.ps1 [command] [args]
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

# 尽早设置控制台与 Python 全局 UTF-8 编码
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"

# 处理子命令
if ($RemainingArgs.Count -gt 0) {
    $cmd = $RemainingArgs[0].ToLower()
    switch ($cmd) {
        "backend" { $Backend = $true }
        "frontend" { $Frontend = $true }
        "worker" { $WorkerOnly = $true }
        "all" { $WithWorker = $true }
        default {
            if ($cmd -match "^\d+$") {
                $Port = [int]$cmd
            } else {
                Write-Host "[ERROR] 未知命令: $cmd" -ForegroundColor Red
                Write-Host "常用命令: .\start_dev.ps1 [backend|frontend|worker|all]" -ForegroundColor Yellow
                exit 1
            }
        }
    }
}

if ($Help) {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host " QuantAgent-Invest 智能投研系统启动指南" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "【常用命令】" -ForegroundColor Yellow
    Write-Host "  .\start_dev.ps1              # 默认启动后端 API（推荐，极简单进程，端口 8000）"
    Write-Host "  .\start_dev.ps1 frontend     # 启动前端开发调试服务器 (Vite)"
    Write-Host "  .\start_dev.ps1 -WithWorker  # 启动后端 API + 独立任务 Worker（双进程分布式模式）"
    Write-Host "  .\start_dev.ps1 worker       # 仅启动 Worker 服务 (端口 8001)"
    Write-Host ""
    Write-Host "【参数选项】" -ForegroundColor Yellow
    Write-Host "  -Port 8000                  # 自定义后端端口 (默认 8000)"
    Write-Host "  -WorkerPort 8001            # 自定义 Worker 端口 (默认 8001)"
    Write-Host "  -NoReload                   # 生产稳定模式（禁用自动重载）"
    Write-Host ""
    exit 0
}

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# 1. 启动前端
if ($Frontend) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "正在启动前端开发服务器 (Vite)..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Push-Location "$root\frontend"
    try {
        npm run dev
    } finally {
        Pop-Location
    }
    exit $LASTEXITCODE
}

# 2. 探测 Python 解释器
$pythonExe = $null
$venvPaths = @(
    (Join-Path $root "env\Scripts\python.exe"),
    (Join-Path $root "venv\Scripts\python.exe"),
    (Join-Path $root "vendors\python\python.exe")
)

foreach ($path in $venvPaths) {
    if (Test-Path $path) {
        $pythonExe = $path
        break
    }
}

if (-not $pythonExe) {
    $pythonExe = "python"
    Write-Host "[WARN] 未检测到本地虚拟环境，使用系统 Python: $pythonExe" -ForegroundColor Yellow
} else {
    Write-Host "[OK] 使用虚拟环境 Python: $pythonExe" -ForegroundColor Green
}

# 检查后端入口
$backendMain = Join-Path $root "app\main.py"
if (-not (Test-Path $backendMain)) {
    Write-Host "[ERROR] 未找到后端入口文件: $backendMain" -ForegroundColor Red
    exit 1
}

# 3. 仅启动 Worker 服务
if ($WorkerOnly) {
    $workerApp = Join-Path $root "app\worker\worker_app.py"
    if (-not (Test-Path $workerApp)) {
        Write-Host "[ERROR] 未找到 Worker 入口: $workerApp" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "启动异步任务 Worker 服务" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  服务端口: $WorkerPort" -ForegroundColor Gray
    Write-Host "  健康检查: http://127.0.0.1:$WorkerPort/health" -ForegroundColor Gray
    Write-Host ""
    & $pythonExe -m uvicorn app.worker.worker_app:app --host 127.0.0.1 --port $WorkerPort --log-level info
    exit $LASTEXITCODE
}

# 4. 双进程模式：后端 API + 独立任务 Worker（当显式指定 -WithWorker 或 all 时触发）
if ($WithWorker) {
    $workerApp = Join-Path $root "app\worker\worker_app.py"
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "启动分布式双进程模式：Backend (端口 $Port) + Worker (端口 $WorkerPort)" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""

    $jobs = @()
    try {
        Write-Host "[1/2] 启动 Backend API 服务..." -ForegroundColor Yellow
        $backendJob = Start-Job -ScriptBlock {
            param($pythonExe, $port, $root)
            Set-Location $root
            $env:PYTHONIOENCODING = "utf-8"
            $env:PYTHONUTF8 = "1"
            $env:PYTHONUNBUFFERED = "1"
            & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $port --log-level info
        } -ArgumentList $pythonExe, $Port, $root
        $jobs += $backendJob
        Write-Host "[OK] Backend API 已启动 (Job ID: $($backendJob.Id)) -> http://127.0.0.1:$Port" -ForegroundColor Green

        Start-Sleep -Seconds 1

        Write-Host "[2/2] 启动 Worker 服务..." -ForegroundColor Yellow
        $workerJob = Start-Job -ScriptBlock {
            param($pythonExe, $workerPort, $root)
            Set-Location $root
            $env:PYTHONIOENCODING = "utf-8"
            $env:PYTHONUTF8 = "1"
            $env:PYTHONUNBUFFERED = "1"
            & $pythonExe -m uvicorn app.worker.worker_app:app --host 127.0.0.1 --port $workerPort --log-level info
        } -ArgumentList $pythonExe, $WorkerPort, $root
        $jobs += $workerJob
        Write-Host "[OK] Worker 服务已启动 (Job ID: $($workerJob.Id)) -> http://127.0.0.1:$WorkerPort" -ForegroundColor Green

        Write-Host ""
        Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
        Write-Host ""

        while ($true) {
            foreach ($job in $jobs) {
                $output = Receive-Job -Job $job -ErrorAction SilentlyContinue
                if ($output) {
                    foreach ($line in $output) { Write-Host $line }
                }
            }
            Start-Sleep -Milliseconds 200
        }
    } finally {
        Write-Host "`n[INFO] 正在停止后台服务..." -ForegroundColor Yellow
        foreach ($job in $jobs) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[OK] 所有后台服务已停止" -ForegroundColor Green
    }
    exit 0
}

# 5. 默认模式：单进程直出极简启动（强烈推荐）
# 直接前台运行 Backend API，实时输出彩色日志，毫秒级响应 Ctrl+C，任务由内置协程池无阻塞处理
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "QuantAgent-Invest 智能投研系统后端启动中..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  服务地址: http://127.0.0.1:$Port" -ForegroundColor Gray
Write-Host "  接口文档: http://127.0.0.1:$Port/docs" -ForegroundColor Gray
Write-Host "  运行模式: 内置异步任务协程池 (极简单进程，无需多端口/独立Worker)" -ForegroundColor Gray
Write-Host ""
Write-Host "提示: 按 Ctrl+C 即可安全退出服务" -ForegroundColor Yellow
Write-Host ""

if ($NoReload) {
    & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $Port --log-level info
} else {
    & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload --log-level info
}
