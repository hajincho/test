# Usage: powershell -File run_ue_probe.ps1 -ScriptPath <lyra_*.py> -Tag <tag> -Done <json path that gets "done": true> [-Timeout 300] [-Visible]
# Launches the editor from the command line (-ExecCmds), runs the probe, moves the window off-screen (no mouse/keyboard automation),
# waits for the json to contain "done": true, then closes the editor.
param([string]$ScriptPath, [string]$Tag = 'bg', [string]$Done, [int]$Timeout = 300, [switch]$Visible)
$ErrorActionPreference = 'Continue'
$ue = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$proj = 'C:\Users\fromj\Downloads\test\test\abc\LyraStarterGame.uproject'
$ini = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'UnrealEngine\5.8\Saved\Config\WindowsEditor\EditorSettings.ini'
if (Test-Path $ini) {
  $txt = Get-Content $ini -Raw
  if ($txt -notmatch 'bThrottleCPUWhenNotForeground') { Add-Content $ini "`n[/Script/UnrealEd.EditorPerformanceSettings]`nbThrottleCPUWhenNotForeground=False`n" }
  else { (Get-Content $ini) -replace 'bThrottleCPUWhenNotForeground=True', 'bThrottleCPUWhenNotForeground=False' | Set-Content $ini }
}
Get-Process UnrealEditor, CrashReportClientEditor -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 4
if ($Done -and (Test-Path $Done)) { Remove-Item $Done -Force }
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W { [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int cx, int cy, uint f); }
"@
$cmd = 'py ' + $ScriptPath + ' ' + $Tag
$p = Start-Process $ue -ArgumentList ('"' + $proj + '"'), ('-ExecCmds="' + $cmd + '"'), '-NoSplash' -PassThru
$t0 = Get-Date; $moved = $false
while (((Get-Date) - $t0).TotalSeconds -lt $Timeout) {
  Start-Sleep 3
  if (-not $Visible -and -not $moved) {
    $q = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
    if ($q -and $q.MainWindowHandle -ne 0 -and $q.MainWindowTitle -like '*LyraStarterGame*') { [W]::SetWindowPos($q.MainWindowHandle, [IntPtr]::Zero, 6000, 0, 1600, 900, 0x0010) | Out-Null; $moved = $true }
  }
  if ($Done -and (Test-Path $Done) -and ((Get-Content $Done -Raw) -match '"done": true')) { break }
  if ($p.HasExited) { break }
}
Start-Sleep 3
Get-Process UnrealEditor, CrashReportClientEditor -ErrorAction SilentlyContinue | Stop-Process -Force
'probe finished: ' + $Tag + ' elapsed ' + [int]((Get-Date) - $t0).TotalSeconds
