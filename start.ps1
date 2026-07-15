# GestureVision Launcher - Clean start every time
Write-Host "Cleaning up stale processes..." -ForegroundColor Yellow

function Kill-ProcessesOnPort {
    param([int]$Port)

    $procs = netstat -ano | Select-String ":$Port\s" | ForEach-Object {
        ($_.ToString().Trim() -split '\s+')[-1]
    } | Sort-Object -Unique

    foreach ($procId in $procs) {
        if ($procId -match '^\d+$' -and [int]$procId -gt 0) {
            try {
                taskkill /F /PID $procId /T 2>&1 | Out-Null
                Write-Host "  Killed PID $procId on port $Port" -ForegroundColor DarkGray
            } catch {}
        }
    }
}

Kill-ProcessesOnPort -Port 8765   # Python backend
Kill-ProcessesOnPort -Port 5173   # Vite

Start-Sleep -Seconds 2

# Verify ports are actually free before proceeding
$stillBusy = @()
foreach ($port in @(8765, 5173)) {
    $check = netstat -ano | Select-String ":$port\s"
    if ($check) { $stillBusy += $port }
}

if ($stillBusy.Count -gt 0) {
    Write-Host "Warning: port(s) still in use: $($stillBusy -join ', ')" -ForegroundColor Red
    Write-Host "Retrying cleanup once more..." -ForegroundColor Yellow
    foreach ($port in $stillBusy) { Kill-ProcessesOnPort -Port $port }
    Start-Sleep -Seconds 2
}

Write-Host "Ports cleared. Starting GestureVision..." -ForegroundColor Green

Set-Location "$PSScriptRoot\frontend"
npm run electron:dev
