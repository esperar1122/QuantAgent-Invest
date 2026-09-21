# QuantAgent-Invest Development Startup Script
# 智能投研系统一键开发全栈启动脚本

[CmdletBinding(PositionalBinding=$false)]
param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$WithWorker,
    [switch]$WorkerOnly,
    [int]$Port = 8000,
    [int]$FrontendPort = 3000,
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
        "backend"  { $BackendOnly = $true }
        "frontend" { $FrontendOnly = $true }
        "worker"   { $WorkerOnly = $true }
        "all"      { } # 默认模式即同时启动前后端
        default {
            if ($cmd -match "^\d+$") {
                $Port = [int]$cmd
            } else {
                Write-Host "[ERROR] 未知命令: $cmd" -ForegroundColor Red
                Write-Host "常用命令: .\start_dev.ps1 [all|backend|frontend|worker]" -ForegroundColor Yellow
                exit 1
            }
        }
    }
}

if ($Help) {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host " QuantAgent-Invest 智能投研系统全栈启动指南" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "【常用命令】" -ForegroundColor Yellow
    Write-Host "  .\start_dev.ps1              # 一键同时启动 前端(3000) + 后端API(8000)"
    Write-Host "  .\start_dev.ps1 -WithWorker  # 一键同时启动 前端 + 后端 + 独立计算Worker"
    Write-Host "  .\start_dev.ps1 backend      # 仅启动后端 API 服务"
    Write-Host "  .\start_dev.ps1 frontend     # 仅启动前端开发服务器 (Vite)"
    Write-Host "  .\start_dev.ps1 worker       # 仅启动 Worker 服务 (端口 8001)"
    Write-Host ""
    Write-Host "【参数选项】" -ForegroundColor Yellow
    Write-Host "  -Port 8000                  # 自定义后端端口 (默认 8000)"
    Write-Host "  -FrontendPort 3000          # 自定义前端端口 (默认 3000)"
    Write-Host "  -WorkerPort 8001            # 自定义 Worker 端口 (默认 8001)"
    Write-Host "  -NoReload                   # 生产稳定模式（禁用后端热重载）"
    Write-Host ""
    exit 0
}

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# 1. 探测 Python 解释器
$pythonExe = $null
$venvPaths = @(
    (Join-Path $root "venv\Scripts\python.exe"),
    (Join-Path $root "env\Scripts\python.exe"),
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

# 2. 进程管理辅助函数
function Stop-PortProcess([int]$targetPort, [string]$label) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $targetPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
        if ($conns) {
            foreach ($c in $conns) {
                $pidToKill = $c.OwningProcess
                if ($pidToKill -gt 0 -and $pidToKill -ne $PID) {
                    Write-Host "[WARN] 端口 $targetPort ($label) 被旧进程 (PID: $pidToKill) 占用，正在释放..." -ForegroundColor Yellow
                    cmd /c "taskkill /F /T /PID $pidToKill >nul 2>nul"
                }
            }
            Start-Sleep -Milliseconds 400
        }
    } catch {}
}

function Stop-ProcessTree([int]$targetPid) {
    if ($targetPid -gt 0) {
        cmd /c "taskkill /F /T /PID $targetPid >nul 2>nul"
    }
}

# 3. 仅启动前端分支
if ($FrontendOnly) {
    Stop-PortProcess $FrontendPort "前端 Vite"
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "正在启动前端开发服务器 (Vite)..." -ForegroundColor Cyan
    Write-Host "  访问地址: http://localhost:$FrontendPort" -ForegroundColor Gray
    Write-Host "========================================" -ForegroundColor Cyan
    Push-Location "$root\frontend"
    try {
        npm run dev -- --port $FrontendPort
    } finally {
        Pop-Location
    }
    exit $LASTEXITCODE
}

# 4. 仅启动 Worker 分支
if ($WorkerOnly) {
    $workerApp = Join-Path $root "app\worker\worker_app.py"
    if (-not (Test-Path $workerApp)) {
        Write-Host "[ERROR] 未找到 Worker 入口: $workerApp" -ForegroundColor Red
        exit 1
    }
    Stop-PortProcess $WorkerPort "Worker 服务"
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "启动异步任务 Worker 服务" -ForegroundColor Cyan
    Write-Host "  服务端口: $WorkerPort" -ForegroundColor Gray
    Write-Host "  健康检查: http://127.0.0.1:$WorkerPort/health" -ForegroundColor Gray
    Write-Host "========================================" -ForegroundColor Cyan
    & $pythonExe -m uvicorn app.worker.worker_app:app --host 127.0.0.1 --port $WorkerPort --log-level info
    exit $LASTEXITCODE
}

# 5. 仅启动后端 API 分支
if ($BackendOnly) {
    Stop-PortProcess $Port "后端 API"
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "QuantAgent-Invest 后端 API 启动中..." -ForegroundColor Cyan
    Write-Host "  服务地址: http://127.0.0.1:$Port" -ForegroundColor Gray
    Write-Host "  接口文档: http://127.0.0.1:$Port/docs" -ForegroundColor Gray
    Write-Host "========================================================" -ForegroundColor Cyan
    if ($NoReload) {
        & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $Port --log-level info
    } else {
        & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload --log-level info
    }
    exit $LASTEXITCODE
}

# 6. 【默认核心模式】：一键同时启动 前端 (Vite) + 后端 API (FastAPI)
Stop-PortProcess $Port "后端 API"
Stop-PortProcess $FrontendPort "前端 Vite"
if ($WithWorker) { Stop-PortProcess $WorkerPort "Worker" }

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  QuantAgent-Invest 正在一键启动前后端全栈服务..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 启动后端 API 进程
$backendArgs = "-m uvicorn app.main:app --host 127.0.0.1 --port $Port --log-level info"
if (-not $NoReload) {
    $backendArgs += " --reload"
}
$backendInfo = New-Object System.Diagnostics.ProcessStartInfo
$backendInfo.FileName = $pythonExe
$backendInfo.Arguments = $backendArgs
$backendInfo.WorkingDirectory = $root
$backendInfo.UseShellExecute = $false
$backendInfo.RedirectStandardOutput = $true
$backendInfo.RedirectStandardError = $true
$backendInfo.CreateNoWindow = $true

$backendProc = New-Object System.Diagnostics.Process
$backendProc.StartInfo = $backendInfo

Register-ObjectEvent -InputObject $backendProc -EventName "OutputDataReceived" -Action {
    if ($EventArgs.Data) { Write-Host "[API] $($EventArgs.Data)" -ForegroundColor Cyan }
} | Out-Null
Register-ObjectEvent -InputObject $backendProc -EventName "ErrorDataReceived" -Action {
    if ($EventArgs.Data) { Write-Host "[API] $($EventArgs.Data)" -ForegroundColor Cyan }
} | Out-Null

$backendProc.Start() | Out-Null
$backendProc.BeginOutputReadLine()
$backendProc.BeginErrorReadLine()
Write-Host "[1/2] 后端 API 服务已就绪 (PID: $($backendProc.Id))" -ForegroundColor Green

# 稍等后端完成基础网络监听初始化
Start-Sleep -Milliseconds 1500

# 启动前端 Vite 进程
$frontendInfo = New-Object System.Diagnostics.ProcessStartInfo
$frontendInfo.FileName = "cmd.exe"
$frontendInfo.Arguments = "/c npm run dev -- --port $FrontendPort"
$frontendInfo.WorkingDirectory = "$root\frontend"
$frontendInfo.UseShellExecute = $false
$frontendInfo.RedirectStandardOutput = $true
$frontendInfo.RedirectStandardError = $true
$frontendInfo.CreateNoWindow = $true

$frontendProc = New-Object System.Diagnostics.Process
$frontendProc.StartInfo = $frontendInfo

Register-ObjectEvent -InputObject $frontendProc -EventName "OutputDataReceived" -Action {
    if ($EventArgs.Data) { Write-Host "[Web] $($EventArgs.Data)" -ForegroundColor Magenta }
} | Out-Null
Register-ObjectEvent -InputObject $frontendProc -EventName "ErrorDataReceived" -Action {
    if ($EventArgs.Data) { Write-Host "[Web] $($EventArgs.Data)" -ForegroundColor Magenta }
} | Out-Null

$frontendProc.Start() | Out-Null
$frontendProc.BeginOutputReadLine()
$frontendProc.BeginErrorReadLine()
Write-Host "[2/2] 前端开发服务已就绪 (PID: $($frontendProc.Id))" -ForegroundColor Green

# 可选独立计算 Worker
$workerProc = $null
if ($WithWorker) {
    $workerInfo = New-Object System.Diagnostics.ProcessStartInfo
    $workerInfo.FileName = $pythonExe
    $workerInfo.Arguments = "-m uvicorn app.worker.worker_app:app --host 127.0.0.1 --port $WorkerPort --log-level info"
    $workerInfo.WorkingDirectory = $root
    $workerInfo.UseShellExecute = $false
    $workerInfo.RedirectStandardOutput = $true
    $workerInfo.RedirectStandardError = $true
    $workerInfo.CreateNoWindow = $true

    $workerProc = New-Object System.Diagnostics.Process
    $workerProc.StartInfo = $workerInfo

    Register-ObjectEvent -InputObject $workerProc -EventName "OutputDataReceived" -Action {
        if ($EventArgs.Data) { Write-Host "[Worker] $($EventArgs.Data)" -ForegroundColor Blue }
    } | Out-Null

    $workerProc.Start() | Out-Null
    $workerProc.BeginOutputReadLine()
    $workerProc.BeginErrorReadLine()
    Write-Host "[Worker] 独立计算工作进程已启动 (PID: $($workerProc.Id))" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  QuantAgent-Invest 全栈系统已一键成功启动！" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  🌐 前端投研终端: http://localhost:$FrontendPort" -ForegroundColor Yellow
Write-Host "  🔌 后端 API 服务: http://127.0.0.1:$Port" -ForegroundColor Cyan
Write-Host "  📚 Swagger 接口: http://127.0.0.1:$Port/docs" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  提示: 按 Ctrl+C 即可同时安全退出前后端所有服务" -ForegroundColor Gray
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

try {
    while (-not $backendProc.HasExited -and -not $frontendProc.HasExited) {
        Start-Sleep -Milliseconds 300
    }
} finally {
    Write-Host "`n[INFO] 正在安全停止前后端服务..." -ForegroundColor Yellow
    Stop-ProcessTree $backendProc.Id
    Stop-ProcessTree $frontendProc.Id
    if ($workerProc) { Stop-ProcessTree $workerProc.Id }
    Get-EventSubscriber | Unregister-Event -ErrorAction SilentlyContinue
    Write-Host "[OK] 前后端所有服务已安全退出。" -ForegroundColor Green
}
