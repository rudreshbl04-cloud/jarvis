# ==============================================================================
# JARVIS Windows Task Scheduler Installer & Uninstaller
# ==============================================================================
param(
    [switch]$Uninstall
)

$TaskName = "JarvisAutoStart"
$WorkingDirectory = (Resolve-Path "$PSScriptRoot\..").Path
$ScriptPath = Join-Path $PSScriptRoot "start_jarvis.ps1"

if ($Uninstall) {
    Write-Host "Checking for existing scheduled task: $TaskName..."
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[UNINSTALL] Scheduled task $TaskName removed successfully."
    } else {
        Write-Host "[UNINSTALL] Task $TaskName was not found."
    }
    exit 0
}

Write-Host "Configuring Windows Task Scheduler for $TaskName..."

# Action: Launch start_jarvis.ps1 hidden via powershell.exe
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`"" `
    -WorkingDirectory $WorkingDirectory

# Trigger: At user logon for current user
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings: run on battery, do not stop, execution limit
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
    -MultipleInstances IgnoreNew

# Principal
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Register or update
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Starts Ollama, verifies models, starts JARVIS server, and opens browser interface at logon." `
    -Force | Out-Null

$verify = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($verify) {
    Write-Host "[INSTALL: PASS] Scheduled task '$TaskName' registered successfully."
    Write-Host "State: $($verify.State)"
    Write-Host "Action: $($verify.Actions.Execute) $($verify.Actions.Arguments)"
    Write-Host "Trigger: AtLogOn ($($verify.Triggers.UserId))"
    exit 0
} else {
    Write-Error "[INSTALL: FAIL] Failed to register task '$TaskName'."
    exit 1
}
