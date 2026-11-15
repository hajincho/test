$sig = '[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c); [DllImport("user32.dll")] public static extern void keybd_event(byte a, byte b, uint c, UIntPtr d);'
Add-Type -MemberDefinition $sig -Name W -Namespace U -ErrorAction SilentlyContinue
$p = Get-Process UnrealEditor | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
[U.W]::keybd_event(0x12,0,0,[UIntPtr]::Zero); [U.W]::ShowWindow($p.MainWindowHandle, 3) | Out-Null; [U.W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null; [U.W]::keybd_event(0x12,0,2,[UIntPtr]::Zero)
