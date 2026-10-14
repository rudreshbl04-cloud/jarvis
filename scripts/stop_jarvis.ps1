# ==============================================================================
# JARVIS Safe Process Terminator
# Stops ONLY the python processes running jarvis.py or bound to port 5000.
# Preserves all other python, IDE, or system tasks.
# ==============================================================================
$ErrorActionPreference = "Continue"

Write-Host "Searching for JARVIS server processes..."

# 1. Check process listening on port 5000
$portConns = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
if ($portConns) {
    foreach ($conn in $portConns) {
        $pidToStop = $conn.OwningProcess
        if ($pidToStop -gt 0) {
            $proc = Get-Process -Id $pidToStop -ErrorAction SilentlyContinue
            if ($proc -and ($proc.Name -like "*python*")) {
                Write-Host "Terminating JARVIS server on port 5000: PID $pidToStop ($($proc.Name))"
                Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

# 2. Check any process whose command line contains jarvis.py
$procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { 
    ($_.Name -like "python*") -and ($_.CommandLine -like "*jarvis.py*")
}

if ($procs) {
    foreach ($p in $procs) {
        Write-Host "Terminating JARVIS process ID: $($p.ProcessId) ($($p.Name))"
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "JARVIS process termination complete."
