# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Stats Endpoint
# =============================================================================
# Description:
#   Returns RAM, CPU, disk and GPU usage.
#   Uses psutil for RAM/CPU/disk; pynvml for NVIDIA GPU (optional).
#   Also reports per-process stats for the current Python process.
#
# File: src/api/endpoints/system_stats.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Changes in 0.6.1:
#   - Added ram_available_mb, ram_pct
#   - Added disk_used_gb, disk_total_gb, disk_pct
#   - Added process stats: proc_ram_mb, proc_cpu_pct, proc_threads
#   - Added GPU stats via pynvml: gpu_name, gpu_ram_used_mb, gpu_ram_total_mb, gpu_pct
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["system"])

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False
    logger.warning("⚠️ psutil not installed — /system/stats will return nulls")

try:
    import pynvml
    pynvml.nvmlInit()
    _NVML = True
except Exception:
    _NVML = False

_proc = psutil.Process(os.getpid()) if _PSUTIL else None


def _gpu_stats() -> list:
    """Collect per-GPU stats via pynvml.

    Returns:
        list: Each item has name, ram_used_mb, ram_total_mb, ram_pct, gpu_pct.
    """
    if not _NVML:
        return []
    gpus = []
    try:
        count = pynvml.nvmlDeviceGetCount()
        for i in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name   = pynvml.nvmlDeviceGetName(handle)
            mem    = pynvml.nvmlDeviceGetMemoryInfo(handle)
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_pct = util.gpu
            except Exception:
                gpu_pct = None
            gpus.append({
                "index":        i,
                "name":         name if isinstance(name, str) else name.decode(),
                "ram_used_mb":  round(mem.used  / 1024 / 1024, 1),
                "ram_total_mb": round(mem.total / 1024 / 1024, 1),
                "ram_pct":      round(mem.used / mem.total * 100, 1) if mem.total else None,
                "gpu_pct":      gpu_pct,
            })
    except Exception as e:
        logger.debug(f"pynvml error: {e}")
    return gpus


@router.get("/stats")
async def system_stats() -> dict:
    """RAM, CPU, disk and GPU usage.

    Returns:
        dict: success, ram_used_mb, ram_available_mb, ram_total_mb, ram_pct,
              cpu_pct, disk_used_gb, disk_total_gb, disk_pct,
              proc_ram_mb, proc_cpu_pct, proc_threads,
              gpus (list).
    """
    if not _PSUTIL:
        return {
            "success": True,
            "ram_used_mb": None, "ram_available_mb": None,
            "ram_total_mb": None, "ram_pct": None,
            "cpu_pct": None,
            "disk_used_gb": None, "disk_total_gb": None, "disk_pct": None,
            "proc_ram_mb": None, "proc_cpu_pct": None, "proc_threads": None,
            "gpus": [],
        }

    mem  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    proc_ram_mb   = None
    proc_cpu_pct  = None
    proc_threads  = None
    if _proc:
        try:
            proc_ram_mb  = round(_proc.memory_info().rss / 1024 / 1024, 1)
            proc_cpu_pct = _proc.cpu_percent(interval=None)
            proc_threads = _proc.num_threads()
        except Exception:
            pass

    return {
        "success":          True,
        # System RAM
        "ram_used_mb":      round(mem.used      / 1024 / 1024, 1),
        "ram_available_mb": round(mem.available / 1024 / 1024, 1),
        "ram_total_mb":     round(mem.total     / 1024 / 1024, 1),
        "ram_pct":          mem.percent,
        # CPU
        "cpu_pct":          psutil.cpu_percent(interval=0.2),
        # Disk (root / on Linux, C:\ on Windows)
        "disk_used_gb":     round(disk.used  / 1024 / 1024 / 1024, 2),
        "disk_total_gb":    round(disk.total / 1024 / 1024 / 1024, 2),
        "disk_pct":         disk.percent,
        # Current process
        "proc_ram_mb":      proc_ram_mb,
        "proc_cpu_pct":     proc_cpu_pct,
        "proc_threads":     proc_threads,
        # GPU
        "gpus":             _gpu_stats(),
    }
