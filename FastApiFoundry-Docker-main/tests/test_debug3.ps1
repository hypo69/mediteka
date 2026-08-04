$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'foundry'
$psi.Arguments = 'service status'
$psi.UseShellExecute = $true
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false
$psi.CreateNoWindow = $true

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$null = $proc.Start()
$proc.WaitForExit()

Write-Host "Exit code: $($proc.ExitCode)"
