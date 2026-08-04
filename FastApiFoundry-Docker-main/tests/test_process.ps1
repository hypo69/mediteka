$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'foundry'
$psi.Arguments = 'service status'
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$null = $proc.Start()
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
Write-Host 'STDOUT:'
Write-Host $stdout
Write-Host 'STDERR:'
Write-Host $stderr
