@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title JARVIS ARC 3.0 - Health Check
cls

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$code = (Get-Content -LiteralPath '%~f0' | Select-Object -Skip 11) -join [Environment]::NewLine; Invoke-Expression $code"
echo.
pause
exit /b
rem ==================== POWERSHELL EXECUTION STARTS ON LINE 12 ====================
$ErrorActionPreference = "Continue"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "               JARVIS ARC 3.0 / RUBI CORE -- HEALTH CHECK              " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Timestamp    : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Project Root : $PWD"
Write-Host ""

$results = @{
    "check1" = "FAIL"
    "check2" = "FAIL"
    "check3" = "WARN"
    "check4" = "FAIL"
}
$counts = @{
    "PASS" = 0
    "FAIL" = 0
    "WARN" = 0
}

# ----------------------------------------------------------------------
# CHECK 1 -- Server process (Port 5000 listener)
# ----------------------------------------------------------------------
Write-Host "[CHECK 1] Server Process (Port 5000 Listener)" -ForegroundColor Yellow
$listenerPid = $null
$listenerProc = $null

try {
    $conn = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        $listenerPid = $conn.OwningProcess
        $listenerProc = Get-Process -Id $listenerPid -ErrorAction SilentlyContinue
    }
} catch {
    try {
        $netstatOut = netstat -ano | Select-String ":5000\s+.*LISTENING\s+(\d+)"
        if ($netstatOut -and $netstatOut.Matches) {
            $listenerPid = [int]$netstatOut.Matches[0].Groups[1].Value
            $listenerProc = Get-Process -Id $listenerPid -ErrorAction SilentlyContinue
        }
    } catch {}
}

if ($listenerPid -and $listenerProc) {
    Write-Host "  Port 5000 Status : LISTENING" -ForegroundColor Green
    Write-Host "  Process PID      : $listenerPid"
    Write-Host "  Process Name     : $($listenerProc.Name)"
    Write-Host "  Executable Path  : $($listenerProc.Path)"
    $results["check1"] = "PASS"
    $counts["PASS"]++
    Write-Host "  Result           : PASS" -ForegroundColor Green
} else {
    Write-Host "  Port 5000 Status : NOT LISTENING (No active listener found)" -ForegroundColor Red
    $results["check1"] = "FAIL"
    $counts["FAIL"]++
    Write-Host "  Result           : FAIL" -ForegroundColor Red
}
Write-Host ""

# ----------------------------------------------------------------------
# CHECK 2 -- Health endpoint (http://127.0.0.1:5000/health)
# ----------------------------------------------------------------------
Write-Host "[CHECK 2] Health Endpoint (http://127.0.0.1:5000/health)" -ForegroundColor Yellow
$healthUrl = "http://127.0.0.1:5000/health"
$healthStatus = $null
$healthBody = ""
$healthError = ""

try {
    $hReq = [System.Net.HttpWebRequest]::Create($healthUrl)
    $hReq.Timeout = 3000
    $hReq.Method = "GET"
    $hResp = $hReq.GetResponse()
    $healthStatus = [int]$hResp.StatusCode
    $hReader = New-Object System.IO.StreamReader($hResp.GetResponseStream())
    $healthBody = $hReader.ReadToEnd()
    $hReader.Close()
    $hResp.Close()
} catch [System.Net.WebException] {
    if ($_.Response) {
        $healthStatus = [int]$_.Response.StatusCode
        $hReader = New-Object System.IO.StreamReader($_.Response.GetResponseStream())
        $healthBody = $hReader.ReadToEnd()
        $hReader.Close()
    } else {
        $healthError = $_.Message
    }
} catch {
    $healthError = $_.Message
}

Write-Host "  Target URL       : $healthUrl"
if ($healthStatus) {
    Write-Host "  HTTP Status Code : $healthStatus"
} else {
    Write-Host "  HTTP Status Code : Connection failed ($healthError)"
}
if ($healthBody) {
    $bodyTrim = if ($healthBody.Length -gt 250) { $healthBody.Substring(0, 250) + "..." } else { $healthBody }
    Write-Host "  Response Body    : $bodyTrim"
}

if ($healthStatus -eq 200) {
    $results["check2"] = "PASS"
    $counts["PASS"]++
    Write-Host "  Result           : PASS" -ForegroundColor Green
} else {
    $results["check2"] = "FAIL"
    $counts["FAIL"]++
    if ($healthStatus -eq 404) {
        Write-Host "  Explanation      : FAIL -- Endpoint returned HTTP 404. JARVIS ARC 3.0 does not implement a /health route (the application status route is /status)." -ForegroundColor Red
    } elseif ($healthStatus) {
        Write-Host "  Explanation      : FAIL -- Endpoint returned unexpected HTTP $healthStatus." -ForegroundColor Red
    } else {
        Write-Host "  Explanation      : FAIL -- Could not connect to endpoint ($healthError)." -ForegroundColor Red
    }
    Write-Host "  Result           : FAIL" -ForegroundColor Red
}
Write-Host ""

# ----------------------------------------------------------------------
# CHECK 3 -- Running version versus disk
# ----------------------------------------------------------------------
Write-Host "[CHECK 3] Running Version Versus Disk" -ForegroundColor Yellow
$jarvisDiskPath = (Resolve-Path ".\jarvis.py" -ErrorAction SilentlyContinue).Path
$diskMod = ""
$diskHash = ""

if ($jarvisDiskPath -and (Test-Path $jarvisDiskPath)) {
    $diskMod = (Get-Item $jarvisDiskPath).LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    $diskHash = (Get-FileHash -Path $jarvisDiskPath -Algorithm SHA256).Hash
    Write-Host "  Disk File Path   : $jarvisDiskPath"
    Write-Host "  Disk Modified    : $diskMod"
    Write-Host "  Disk SHA-256     : $diskHash"
} else {
    Write-Host "  Disk File Path   : NOT FOUND (jarvis.py missing)" -ForegroundColor Red
}

$procStartTime = ""
$procCmdLine = ""
if ($listenerPid -and $listenerProc) {
    try {
        $procStartTime = $listenerProc.StartTime.ToString("yyyy-MM-dd HH:mm:ss")
    } catch {}
    try {
        $procWmi = Get-CimInstance Win32_Process -Filter "ProcessId = $listenerPid" -ErrorAction SilentlyContinue
        if ($procWmi) { $procCmdLine = $procWmi.CommandLine }
    } catch {}
    Write-Host "  Running Process  : PID $listenerPid ($($listenerProc.Name))"
    Write-Host "  Process Started  : $procStartTime"
    Write-Host "  Executable Path  : $($listenerProc.Path)"
    Write-Host "  Command Line     : $procCmdLine"
} else {
    Write-Host "  Running Process  : None detected on port 5000"
}

# Query application for exposed version/build metadata
$exposedVersion = $null
try {
    $sReq = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:5000/status")
    $sReq.Timeout = 2000
    $sResp = $sReq.GetResponse()
    $sReader = New-Object System.IO.StreamReader($sResp.GetResponseStream())
    $sBody = $sReader.ReadToEnd()
    $sReader.Close()
    $sResp.Close()
    $sObj = $sBody | ConvertFrom-Json
    if ($sObj.version -or $sObj.build) {
        $exposedVersion = "Version: $($sObj.version) Build: $($sObj.build)"
    }
} catch {}

if ($exposedVersion) {
    Write-Host "  App Metadata     : $exposedVersion"
} else {
    Write-Host "  App Metadata     : Application exposes no loaded version or source hash endpoint"
}

Write-Host "  Evaluation       : A disk timestamp or hash alone does not prove which source code a running Python process loaded in memory."
Write-Host "  Result           : WARN -- Cannot conclusively verify that the running process loaded the current jarvis.py." -ForegroundColor Yellow
$results["check3"] = "WARN"
$counts["WARN"]++
Write-Host ""

# ----------------------------------------------------------------------
# CHECK 4 -- One real chat API test ('open calculator')
# ----------------------------------------------------------------------
Write-Host "[CHECK 4] One Real Chat API Test ('open calculator')" -ForegroundColor Yellow
Write-Host "  Side Effect Note : Sending 'open calculator' will attempt to launch Windows Calculator on the host." -ForegroundColor Cyan

$chatSuccess = $false
$chatWarn = $false
$chatStatus = $null
$chatResponseText = ""
$chatErrorMsg = ""

if (-not $listenerPid) {
    Write-Host "  Execution Skipped: Cannot run Chat API test because server is not listening on port 5000." -ForegroundColor Red
    $results["check4"] = "FAIL"
    $counts["FAIL"]++
    Write-Host "  Result           : FAIL" -ForegroundColor Red
} else {
    # 1. Establish cookie container & resolve PIN
    $cookies = New-Object System.Net.CookieContainer
    $pin = "1234"
    if (Test-Path ".\settings.json") {
        try {
            $cfg = Get-Content ".\settings.json" -Raw | ConvertFrom-Json
            if ($cfg.pin) { $pin = $cfg.pin }
        } catch {}
    }

    # 2. Authenticate session via /lock (in case phone/PIN lock is active)
    try {
        $lockReq = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:5000/lock")
        $lockReq.Method = "POST"
        $lockReq.ContentType = "application/json"
        $lockReq.CookieContainer = $cookies
        $lockReq.Timeout = 4000
        $lockPayload = [System.Text.Encoding]::UTF8.GetBytes("{`"pin`":`"$pin`"}")
        $lockReqStream = $lockReq.GetRequestStream()
        $lockReqStream.Write($lockPayload, 0, $lockPayload.Length)
        $lockReqStream.Close()
        $lockResp = $lockReq.GetResponse()
        $lockResp.Close()
    } catch {}

    # 3. Fetch CSRF token from /
    $csrfToken = ""
    try {
        $rootReq = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:5000/")
        $rootReq.Method = "GET"
        $rootReq.CookieContainer = $cookies
        $rootReq.Timeout = 4000
        $rootResp = $rootReq.GetResponse()
        $rootReader = New-Object System.IO.StreamReader($rootResp.GetResponseStream())
        $rootHtml = $rootReader.ReadToEnd()
        $rootReader.Close()
        $rootResp.Close()
        if ($rootHtml -match 'const\s+CSRF\s*=\s*"([^"]+)"') {
            $csrfToken = $matches[1]
        }
    } catch {}

    # 4. Create new session via /new
    $sessionId = ""
    try {
        $newReq = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:5000/new")
        $newReq.Method = "POST"
        $newReq.ContentType = "application/json"
        if ($csrfToken) { $newReq.Headers.Add("X-Jarvis-Token", $csrfToken) }
        $newReq.CookieContainer = $cookies
        $newReq.Timeout = 4000
        $newPayload = [System.Text.Encoding]::UTF8.GetBytes("{}")
        $newReqStream = $newReq.GetRequestStream()
        $newReqStream.Write($newPayload, 0, $newPayload.Length)
        $newReqStream.Close()
        $newResp = $newReq.GetResponse()
        $newReader = New-Object System.IO.StreamReader($newResp.GetResponseStream())
        $newJson = $newReader.ReadToEnd()
        $newReader.Close()
        $newResp.Close()
        $newObj = $newJson | ConvertFrom-Json
        $sessionId = $newObj.id
    } catch {
        $chatErrorMsg = "Failed to create session: $_"
    }

    # 5. Send exactly ONE chat request to /chat
    if ($sessionId) {
        Write-Host "  Chat Session ID  : $sessionId"
        Write-Host "  CSRF Token       : $(if ($csrfToken) { $csrfToken.Substring(0,8) + '...' } else { 'None' })"
        Write-Host "  Test Command     : open calculator"

        try {
            $chatReq = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:5000/chat")
            $chatReq.Method = "POST"
            $chatReq.ContentType = "application/json"
            if ($csrfToken) { $chatReq.Headers.Add("X-Jarvis-Token", $csrfToken) }
            $chatReq.CookieContainer = $cookies
            $chatReq.Timeout = 12000
            
            $payloadObj = @{
                "session" = $sessionId
                "message" = "open calculator"
                "model" = "auto"
                "agentic_mode" = $true
            }
            $chatPayloadStr = $payloadObj | ConvertTo-Json -Compress
            $chatBytes = [System.Text.Encoding]::UTF8.GetBytes($chatPayloadStr)
            $chatReqStream = $chatReq.GetRequestStream()
            $chatReqStream.Write($chatBytes, 0, $chatBytes.Length)
            $chatReqStream.Close()

            $chatResp = $chatReq.GetResponse()
            $chatStatus = [int]$chatResp.StatusCode
            $chatReader = New-Object System.IO.StreamReader($chatResp.GetResponseStream())
            $rawSse = $chatReader.ReadToEnd()
            $chatReader.Close()
            $chatResp.Close()

            # Parse SSE chunks
            $chunks = @()
            $lines = $rawSse -split "`r?`n"
            foreach ($line in $lines) {
                if ($line -match '^data:\s*(.+)$') {
                    $jsonStr = $matches[1]
                    if ($jsonStr -ne '[DONE]') {
                        try {
                            $item = $jsonStr | ConvertFrom-Json
                            if ($item.chunk) { $chunks += $item.chunk }
                            if ($item.error) { $chatErrorMsg = $item.error.message }
                        } catch {}
                    }
                }
            }
            $chatResponseText = ($chunks -join "")
            if (-not $chatResponseText) { $chatResponseText = $rawSse }

        } catch [System.Net.WebException] {
            if ($_.Response) {
                $chatStatus = [int]$_.Response.StatusCode
                $errReader = New-Object System.IO.StreamReader($_.Response.GetResponseStream())
                $chatResponseText = $errReader.ReadToEnd()
                $errReader.Close()
            } else {
                $chatErrorMsg = $_.Message
            }
        } catch {
            $chatErrorMsg = $_.Message
        }

        Write-Host "  HTTP Status Code : $(if ($chatStatus) { $chatStatus } else { 'Connection Error' })"
        $displayResp = if ($chatResponseText.Length -gt 250) { $chatResponseText.Substring(0, 250) + "..." } else { $chatResponseText }
        Write-Host "  Response Content : $displayResp"

        # Determine contract outcome
        if ($chatStatus -eq 200 -and $chatResponseText -match '(?i)verified running') {
            Write-Host "  Contract Status  : Verified Execution -- Process confirmed running on host." -ForegroundColor Green
            $chatSuccess = $true
            $results["check4"] = "PASS"
            $counts["PASS"]++
            Write-Host "  Result           : PASS" -ForegroundColor Green
        } elseif ($chatStatus -eq 200 -and ($chatResponseText -match '(?i)(process started|launch request was sent)')) {
            Write-Host "  Contract Status  : Unverified Execution -- Launch requested/process started, but running state not verified." -ForegroundColor Yellow
            $chatWarn = $true
            $results["check4"] = "WARN"
            $counts["WARN"]++
            Write-Host "  Result           : WARN" -ForegroundColor Yellow
        } elseif ($chatStatus -eq 200 -and ($chatResponseText -match '(?i)opened calculator')) {
            Write-Host "  Contract Status  : Accepted & Executed -- Calculator opened." -ForegroundColor Green
            $chatSuccess = $true
            $results["check4"] = "PASS"
            $counts["PASS"]++
            Write-Host "  Result           : PASS" -ForegroundColor Green
        } else {
            Write-Host "  Contract Status  : Execution failure or ambiguous response ($chatErrorMsg)" -ForegroundColor Red
            $results["check4"] = "FAIL"
            $counts["FAIL"]++
            Write-Host "  Result           : FAIL" -ForegroundColor Red
        }
    } else {
        Write-Host "  Execution Failed : Could not establish chat session ($chatErrorMsg)" -ForegroundColor Red
        $results["check4"] = "FAIL"
        $counts["FAIL"]++
        Write-Host "  Result           : FAIL" -ForegroundColor Red
    }
}
Write-Host ""

# ----------------------------------------------------------------------
# FINAL REPORT
# ----------------------------------------------------------------------
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "JARVIS ARC 3.0 -- HEALTH CHECK" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "- [$($results['check1'])] Port 5000 listener"
Write-Host "- [$($results['check2'])] Health endpoint"
Write-Host "- [$($results['check3'])] Running version versus disk"
Write-Host "- [$($results['check4'])] Chat API test"
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "SUMMARY: $($counts['PASS']) PASS, $($counts['FAIL']) FAIL, $($counts['WARN']) WARN" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Troubleshooting hints
if ($counts["FAIL"] -gt 0 -or $counts["WARN"] -gt 0) {
    Write-Host "TROUBLESHOOTING HINTS:" -ForegroundColor Yellow
    if ($results["check1"] -eq "FAIL") {
        Write-Host "  * Port 5000: Start JARVIS by running 'py -3.12 jarvis.py' in project root."
    }
    if ($results["check2"] -eq "FAIL") {
        Write-Host "  * Health Endpoint: Server is active but does not route /health. Check /status instead."
    }
    if ($results["check3"] -eq "WARN") {
        Write-Host "  * Version vs Disk: Restart the server to ensure the running process executes latest jarvis.py."
    }
    if ($results["check4"] -eq "FAIL") {
        Write-Host "  * Chat API: Check Ollama connectivity ('ollama list') and ensure port 5000 is accepting requests."
    }
    Write-Host ""
}
