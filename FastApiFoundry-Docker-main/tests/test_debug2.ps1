$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'foundry'
$psi.Arguments = 'service status'
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.UseShellExecute = $true  # Try with ShellExecute
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$null = $proc.Start()
$proc.WaitForExit()

Write-Host "Exit code: $($proc.ExitCode)"
