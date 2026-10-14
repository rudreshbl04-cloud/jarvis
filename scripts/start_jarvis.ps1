# ==============================================================================
# JARVIS Windows Auto-Start Orchestrator
# ==============================================================================
param(
    [switch]$NoBrowser,
    [switch]$ForceRestart
)

$ErrorActionPreference = "Continue"
$Workspace = (Resolve-Path "$PSScriptRoot\..").Path
$LogFile = "$Workspace\artifacts\verification\auto-start.log"
New-Item -ItemType Directory -Force -Path "$Workspace\artifacts\verification" | Out-Null

function Log([string]$msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$ts] $msg"
    Write-Host $line
    try {
        [System.IO.File]::AppendAllText($LogFile, $line + "`r`n", [System.Text.Encoding]::UTF8)
    } catch {}
}

Log "=== JARVIS Auto-Start Orchestrator Initiated ==="

# 1. Locate Executables
$PythonExe = "$env:LOCALAPPDATA\Microsoft\WindowsApps\pythonw.exe"
if (-not (Test-Path $PythonExe)) {
    if (Test-Path "$env:USERPROFILE\anaconda3\pythonw.exe") {
        $PythonExe = "$env:USERPROFILE\anaconda3\pythonw.exe"
    } else {
        $PythonExe = "pythonw.exe"
    }
}
$OllamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$OllamaApp = "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
$ModelsPath = "$env:USERPROFILE\.ollama\models"
$env:OLLAMA_MODELS = $ModelsPath

Log "Located Python: $PythonExe"
Log "Located Ollama: $OllamaExe"

# Helper: Test HTTP endpoint
function Test-HttpEndpoint([string]$url, [int]$timeoutSec=2) {
    try {
        $req = [System.Net.WebRequest]::Create($url)
        $req.Timeout = $timeoutSec * 1000
        $req.Method = "GET"
        $resp = $req.GetResponse()
        $status = [int]$resp.StatusCode
        $resp.Close()
        return ($status -ge 200 -and $status -lt 400)
    } catch {
        return $false
    }
}

# 2. Ollama Readiness
Log "[STEP 1/5] Checking Ollama Service (port 11434)..."
$ollamaRunning = Test-HttpEndpoint "http://127.0.0.1:11434/api/tags"

if (-not $ollamaRunning) {
    Log "Ollama service not detected. Starting Ollama daemon..."
    if (Test-Path $OllamaExe) {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $OllamaExe
        $psi.Arguments = "serve"
        $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $psi.EnvironmentVariables["OLLAMA_MODELS"] = $ModelsPath
        $psi.EnvironmentVariables["OLLAMA_HOST"] = "127.0.0.1:11434"
        [System.Diagnostics.Process]::Start($psi) | Out-Null
    } elseif (Test-Path $OllamaApp) {
        Start-Process -FilePath $OllamaApp -WindowStyle Hidden -ErrorAction SilentlyContinue
    }

    # Bounded wait for Ollama (max 30s)
    $elapsed = 0
    while ($elapsed -lt 30) {
        Start-Sleep -Seconds 1
        $elapsed++
        if (Test-HttpEndpoint "http://127.0.0.1:11434/api/tags") {
            $ollamaRunning = $true
            break
        }
    }
}

if (-not $ollamaRunning) {
    Log "[ERROR] Ollama service failed to become ready within 30 seconds."
    exit 1
}
Log "[STEP 1/5: PASS] Ollama is online and responsive."

# 3. Model Availability Verification
Log "[STEP 2/5] Verifying configured AI models..."
try {
    $tagsRaw = (Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5)
    $installedModels = $tagsRaw.models | ForEach-Object { $_.name }
    Log "Discovered models: $($installedModels -join ', ')"
    $requiredModel = "qwen2.5:3b"
    if ($installedModels -notcontains $requiredModel -and ($installedModels -notmatch "qwen2.5:3b")) {
        Log "[WARNING] Configured model $requiredModel not found in installed list. Available: $($installedModels -join ', ')"
    } else {
        Log "[STEP 2/5: PASS] Primary chat model ($requiredModel) is verified and available."
    }
} catch {
    Log "[WARNING] Could not parse model tags list: $_"
}

# 4. JARVIS Server Verification & Startup
Log "[STEP 3/5] Checking JARVIS server (port 5000)..."
$serverRunning = Test-HttpEndpoint "http://127.0.0.1:5000/manifest.json"

if ($ForceRestart -and $serverRunning) {
    Log "ForceRestart flag specified. Stopping existing JARVIS instance..."
    & "$Workspace\scripts\stop_jarvis.ps1"
    Start-Sleep -Seconds 2
    $serverRunning = $false
}

if ($serverRunning) {
    Log "[STEP 3/5: PASS] JARVIS server is already healthy and active on port 5000 (Idempotent reuse)."
} else {
    Log "Starting JARVIS server via $PythonExe..."
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $PythonExe
    $psi.Arguments = "`"$Workspace\jarvis.py`""
    $psi.WorkingDirectory = $Workspace
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    [System.Diagnostics.Process]::Start($psi) | Out-Null

    # Bounded wait for server (max 30s)
    $elapsed = 0
    while ($elapsed -lt 30) {
        Start-Sleep -Seconds 1
        $elapsed++
        if (Test-HttpEndpoint "http://127.0.0.1:5000/manifest.json") {
            $serverRunning = $true
            break
        }
    }

    if (-not $serverRunning) {
        Log "[ERROR] JARVIS server failed to start within 30 seconds."
        exit 2
    }
    Log "[STEP 3/5: PASS] JARVIS server started successfully and verified healthy."
}

# 5. Open Browser Interface
$TargetUrl = "http://127.0.0.1:5000"
try {
    $netInfo = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/network-info" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($netInfo.phone_mode -and $netInfo.lan_url) {
        $TargetUrl = $netInfo.lan_url
    }
} catch {}

if (-not $NoBrowser) {
    Log "[STEP 4/5] Opening JARVIS in default browser: $TargetUrl"
    Start-Process $TargetUrl
    Log "[STEP 4/5: PASS] Browser launched."
} else {
    Log "[STEP 4/5: SKIP] NoBrowser flag set."
}

Log "[STEP 5/5: PASS] JARVIS Auto-Start completed successfully. Ready for user interaction."
exit 0
