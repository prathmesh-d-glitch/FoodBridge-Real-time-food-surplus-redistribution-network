# kill_ports.ps1 — kills all FoodBridge microservice ports before restarting
# Usage: powershell -ExecutionPolicy Bypass -File kill_ports.ps1

Write-Host "Killing FoodBridge microservice ports 8001-8006..." -ForegroundColor Yellow

8001,8002,8003,8004,8005,8006 | ForEach-Object {
    $port = $_
    $proc_id = (netstat -ano | Select-String ":$port\s.*LISTENING" | ForEach-Object { ($_ -split '\s+')[-1] })
    if ($proc_id) {
        Stop-Process -Id $proc_id -Force -ErrorAction SilentlyContinue
        Write-Host "  Killed port $port (PID $proc_id)" -ForegroundColor Green
    } else {
        Write-Host "  Port $port already free" -ForegroundColor Gray
    }
}

Start-Sleep -Seconds 1
Write-Host "All ports cleared. You can now run: python dev_servers.py" -ForegroundColor Cyan
