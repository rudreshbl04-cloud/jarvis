' ==============================================================================
' J.A.R.V.I.S. ARC 3.0 - Silent Windows Desktop Launcher
' ==============================================================================
' 1. Verifies/starts local Ollama service with OLLAMA_MODELS set to %USERPROFILE%\.ollama\models.
' 2. Verifies local AI model availability (qwen2.5:3b).
' 3. Single-instance protection: skips starting JARVIS if already healthy on port 5000.
' 4. Starts jarvis.py quietly using pythonw.exe (window style 0, zero console flash).
' 5. Waits for HTTP health check on http://127.0.0.1:5000/manifest.json.
' 6. Opens the default web browser to http://127.0.0.1:5000.
' ==============================================================================

Option Explicit

Dim shell, fso, localAppData, userProfile, scriptDir, envProcess
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
localAppData = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
userProfile = shell.ExpandEnvironmentStrings("%USERPROFILE%")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Set persistent environment for child processes
Set envProcess = shell.Environment("PROCESS")
envProcess("OLLAMA_MODELS") = userProfile & "\.ollama\models"

' Helper: test whether an HTTP endpoint responds with success
Function CheckHttp(url)
    On Error Resume Next
    Dim http
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    If http Is Nothing Then Set http = CreateObject("MSXML2.ServerXMLHTTP")
    http.setTimeouts 2000, 2000, 2000, 2000
    http.open "GET", url, False
    http.send
    If Err.Number = 0 Then
        CheckHttp = (http.Status >= 200 And http.Status < 400)
    Else
        CheckHttp = False
    End If
    On Error GoTo 0
    Set http = Nothing
End Function

' Helper: get response body from HTTP endpoint
Function GetHttpText(url)
    On Error Resume Next
    Dim http
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    If http Is Nothing Then Set http = CreateObject("MSXML2.ServerXMLHTTP")
    http.setTimeouts 3000, 3000, 3000, 3000
    http.open "GET", url, False
    http.send
    If Err.Number = 0 And http.Status = 200 Then
        GetHttpText = http.responseText
    Else
        GetHttpText = ""
    End If
    On Error GoTo 0
    Set http = Nothing
End Function

' ------------------------------------------------------------------------------
' Stage A: Ollama Service Readiness
' ------------------------------------------------------------------------------
If Not CheckHttp("http://127.0.0.1:11434/api/tags") Then
    Dim ollamaApp, ollamaExe
    ollamaApp = localAppData & "\Programs\Ollama\ollama app.exe"
    ollamaExe = localAppData & "\Programs\Ollama\ollama.exe"

    If fso.FileExists(ollamaExe) Then
        shell.Run """" & ollamaExe & """ serve", 0, False
    ElseIf fso.FileExists(ollamaApp) Then
        shell.Run """" & ollamaApp & """", 0, False
    End If

    ' Poll until port 11434 responds (bounded timeout 30 seconds)
    Dim elapsedOllama
    elapsedOllama = 0
    Do While elapsedOllama < 30
        WScript.Sleep 1000
        elapsedOllama = elapsedOllama + 1
        If CheckHttp("http://127.0.0.1:11434/api/tags") Then Exit Do
    Loop

    If Not CheckHttp("http://127.0.0.1:11434/api/tags") Then
        MsgBox "Ollama failed to start within 30 seconds." & vbCrLf & _
               "Please verify that Ollama is installed at: " & ollamaExe, _
               vbExclamation, "JARVIS Launcher Notice"
    End If
End If

' ------------------------------------------------------------------------------
' Stage B: Verify Required Local AI Model
' ------------------------------------------------------------------------------
Dim tagsJson
tagsJson = GetHttpText("http://127.0.0.1:11434/api/tags")
If tagsJson <> "" Then
    If InStr(LCase(tagsJson), "llama3.2:3b") = 0 And InStr(LCase(tagsJson), "qwen2.5:3b") = 0 Then
        MsgBox "Required AI model 'llama3.2:3b' or 'qwen2.5:3b' was not found in Ollama." & vbCrLf & _
               "You can pull it by running in PowerShell: ollama pull llama3.2:3b", _
               vbInformation, "JARVIS Model Notice"
    End If
End If

' ------------------------------------------------------------------------------
' Stage C: JARVIS Single-Instance Protection & Backend Launch
' ------------------------------------------------------------------------------
Dim jarvisRunning
jarvisRunning = CheckHttp("http://127.0.0.1:5000/manifest.json")

If Not jarvisRunning Then
    Dim pythonwExe
    If fso.FileExists(userProfile & "\anaconda3\pythonw.exe") Then
        pythonwExe = userProfile & "\anaconda3\pythonw.exe"
    ElseIf fso.FileExists(localAppData & "\Microsoft\WindowsApps\pythonw.exe") Then
        pythonwExe = localAppData & "\Microsoft\WindowsApps\pythonw.exe"
    Else
        pythonwExe = "pythonw.exe"
    End If

    shell.CurrentDirectory = scriptDir
    shell.Run """" & pythonwExe & """ """ & scriptDir & "\jarvis.py""", 0, False

    ' Poll until http://127.0.0.1:5000 responds (timeout 45 seconds)
    Dim elapsedJarvis
    elapsedJarvis = 0
    Do While elapsedJarvis < 45
        WScript.Sleep 1000
        elapsedJarvis = elapsedJarvis + 1
        If CheckHttp("http://127.0.0.1:5000/manifest.json") Then
            jarvisRunning = True
            Exit Do
        End If
    Loop

    If Not jarvisRunning Then
        MsgBox "JARVIS server failed to respond on http://127.0.0.1:5000 within 45 seconds." & vbCrLf & _
               "Please check " & scriptDir & "\artifacts\verification\auto-start.log for diagnostics.", _
               vbCritical, "JARVIS Startup Timeout"
        WScript.Quit 1
    End If
End If

' ------------------------------------------------------------------------------
' Stage D: Open Application in Dedicated App Window or Browser
' ------------------------------------------------------------------------------
Dim chromeExe, edgeExe, targetUrl
targetUrl = "http://127.0.0.1:5000"
chromeExe = "C:\Program Files\Google\Chrome\Application\chrome.exe"
edgeExe = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

If fso.FileExists(chromeExe) Then
    shell.Run """" & chromeExe & """ --app=" & targetUrl, 1, False
ElseIf fso.FileExists(edgeExe) Then
    shell.Run """" & edgeExe & """ --app=" & targetUrl, 1, False
Else
    shell.Run targetUrl
End If
