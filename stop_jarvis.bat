@echo off
setlocal
echo Stopping Jarvis server...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$killed = $false; " ^
  "try { " ^
  "  $cimProcs = Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { ($_.Name -like 'python*' -or $_.Name -like 'pythonw*') -and $_.CommandLine -like '*jarvis.py*' }; " ^
  "  if ($cimProcs) { " ^
  "    foreach ($p in $cimProcs) { " ^
  "      Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; " ^
  "      Write-Host ('Terminated Jarvis process ID ' + $p.ProcessId); " ^
  "      $killed = $true; " ^
  "    } " ^
  "  } " ^
  "} catch { } " ^
  "if (-not $killed) { " ^
  "  $conns = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue; " ^
  "  if ($conns) { " ^
  "    foreach ($c in $conns) { " ^
  "      if ($c.OwningProcess) { " ^
  "        $pr = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue; " ^
  "        if ($pr -and ($pr.ProcessName -like 'python*' -or $pr.ProcessName -like 'pythonw*')) { " ^
  "          Stop-Process -Id $pr.Id -Force -ErrorAction SilentlyContinue; " ^
  "          Write-Host ('Terminated Jarvis process ID ' + $pr.Id); " ^
  "          $killed = $true; " ^
  "        } " ^
  "      } " ^
  "    } " ^
  "  } " ^
  "} " ^
  "if (-not $killed) { " ^
  "  Write-Host 'Jarvis is not currently running.'; " ^
  "}"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$portFree = $false; " ^
  "for ($i=0; $i -lt 10; $i++) { " ^
  "  $conns = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue; " ^
  "  if (-not $conns) { $portFree = $true; break; } " ^
  "  Start-Sleep -Milliseconds 500; " ^
  "} " ^
  "if ($portFree) { Write-Host 'Port 5000 is now free.' } else { Write-Host 'Waiting for port 5000...' }"

echo Jarvis stopped cleanly.
