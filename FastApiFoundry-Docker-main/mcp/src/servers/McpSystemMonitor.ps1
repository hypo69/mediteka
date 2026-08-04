# =====================================================================
# File: McpSystemMonitor.ps1
# Description: MCP Server for monitoring system resources (CPU, RAM, Disk)
# Author: hypo69
# Protocol: STDIO (JSON-RPC)
# =====================================================================

$ErrorActionPreference = "Stop"

# Функция для отправки JSON-RPC ответов в stdout
function Send-Response {
    param([hashtable]$Response)
    $json = $Response | ConvertTo-Json -Depth 10 -Compress
    [Console]::Out.WriteLine($json)
}

Write-Error "System Monitor MCP Server Started" # Отладка в stderr

while ($true) {
    $line = [Console]::In.ReadLine()
    if ($null -eq $line) { break }

    try {
        $request = $line | ConvertFrom-Json
        $method = $request.method
        $id = $request.id

        switch ($method) {
            "initialize" {
                Send-Response @{
                    jsonrpc = "2.0"
                    id = $id
                    result = @{
                        protocolVersion = "2024-11-05"
                        capabilities = @{}
                        serverInfo = @{ name = "system-monitor"; version = "1.0.0" }
                    }
                }
            }

            "tools/list" {
                Send-Response @{
                    jsonrpc = "2.0"
                    id = $id
                    result = @{
                        tools = @(
                            @{
                                name = "get_system_metrics"
                                description = "Get current CPU load, available memory and disk space"
                                inputSchema = @{ type = "object"; properties = @{} }
                            }
                        )
                    }
                }
            }

            "tools/call" {
                if ($request.params.name -eq "get_system_metrics") {
                    $cpu = Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average
                    $mem = Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory, TotalVisibleMemorySize
                    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object FreeSpace, Size

                    # Сбор сетевой статистики (суммарно по всем активным адаптерам)
                    $netStats = Get-NetAdapterStatistics | Where-Object { $_.Status -eq 'Up' }
                    $netReceivedMB = [Math]::Round(($netStats | Measure-Object -Property ReceivedBytes -Sum).Sum / 1MB, 2)
                    $netSentMB = [Math]::Round(($netStats | Measure-Object -Property SentBytes -Sum).Sum / 1MB, 2)

                    # Попытка получить статус системных кулеров (может быть пусто на некоторых конфигурациях)
                    $sysFans = Get-CimInstance Win32_Fan -ErrorAction SilentlyContinue
                    $fanCount = if ($sysFans) { ($sysFans | Measure-Object).Count } else { 0 }

                    # Сбор данных GPU при наличии nvidia-smi в системе
                    $gpuMetrics = $null
                    $gpuText = ""
                    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
                        $gpuRaw = & nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,fan.speed --format=csv,noheader,nounits
                        $gpuData = $gpuRaw -split ","
                        if ($gpuData.Count -ge 4) {
                            $gpuMetrics = @{
                                temperature = [int]$gpuData[0].Trim()
                                load_percent = [int]$gpuData[1].Trim()
                                memory_used_mb = [int]$gpuData[2].Trim()
                                memory_total_mb = [int]$gpuData[3].Trim()
                                fan_speed_percent = if ($gpuData.Count -gt 4 -and $gpuData[4].Trim() -ne 'N/A') { [int]$gpuData[4].Trim() } else { $null }
                            }
                            $gpuText = "`nGPU: Temp: $($gpuMetrics.temperature)°C, Load: $($gpuMetrics.load_percent)%, Fan: $($gpuMetrics.fan_speed_percent)%"
                        }
                    }

                    $stats = "CPU Load: $cpu%`n" +
                             "RAM Free: $([Math]::Round($mem.FreePhysicalMemory / 1024 / 1024, 2)) GB / $([Math]::Round($mem.TotalVisibleMemorySize / 1024 / 1024, 2)) GB`n" +
                             "Disk C: Free: $([Math]::Round($disk.FreeSpace / 1GB, 2)) GB / $([Math]::Round($disk.Size / 1GB, 2)) GB`n" +
                             "Network: Recv: $netReceivedMB MB, Sent: $netSentMB MB`n" +
                             "System Fans: $fanCount active" +
                             $gpuText

                    Send-Response @{
                        jsonrpc = "2.0"
                        id = $id
                        result = @{
                            content = @(@{ type = "text"; text = $stats })
                            metrics = @{
                                cpu_load = $cpu
                                ram_free_gb = [Math]::Round($mem.FreePhysicalMemory / 1024 / 1024, 2)
                                network = @{ received_mb = $netReceivedMB; sent_mb = $netSentMB }
                                fans = @{ system_active = $fanCount }
                                gpu = $gpuMetrics
                            }
                        }
                    }
                }
            }

            default {
                # Игнорируем неизвестные методы или уведомления
            }
        }
    }
    catch {
        $errorMessage = $_.Exception.Message
        Send-Response @{
            jsonrpc = "2.0"
            id = $id
            error = @{ code = -32603; message = $errorMessage }
        }
    }
}