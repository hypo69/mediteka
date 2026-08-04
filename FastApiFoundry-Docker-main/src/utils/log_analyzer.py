# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Log Analysis and Monitoring System
# =============================================================================
# Описание:
#   Система анализа логов с метриками производительности и мониторингом ошибок
#   Предоставляет API для получения статистики и аналитики
#
# File: log_analyzer.py
# Project: Ai Assistant
# Module: FastApiFoundry
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import re

from .logging_system import get_logger

logger = get_logger("log-analyzer")

class LogAnalyzer:
    """Анализатор логов с метриками и статистикой"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.cache = {}
        self.cache_ttl = 300  # 5 минут
        
    async def get_system_health(self) -> Dict[str, Any]:
        """Получить общее состояние системы на основе логов"""
        logger.debug("Анализ состояния системы")
        
        try:
            # Анализ за последний час
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            errors = await self._count_errors(start_time, end_time)
            warnings = await self._count_warnings(start_time, end_time)
            api_stats = await self._analyze_api_performance(start_time, end_time)
            model_stats = await self._analyze_model_performance(start_time, end_time)
            
            # Определение общего статуса
            if errors > 10:
                status = "critical"
            elif errors > 5 or warnings > 20:
                status = "warning"
            else:
                status = "healthy"
            
            health_data = {
                "status": status,
                "timestamp": end_time,
                "period": "1h",
                "metrics": {
                    "errors_count": errors,
                    "warnings_count": warnings,
                    "api_requests": api_stats.get("total_requests", 0),
                    "avg_response_time": api_stats.get("avg_response_time", 0),
                    "active_models": len(model_stats.get("models", {})),
                    "failed_model_operations": model_stats.get("failed_operations", 0)
                },
                "details": {
                    "api_performance": api_stats,
                    "model_performance": model_stats
                }
            }
            
            logger.info("Анализ состояния системы завершен", 
                       status=status, 
                       errors=errors, 
                       warnings=warnings)
            
            return health_data
            
        except Exception as e:
            logger.exception("Ошибка анализа состояния системы", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    async def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получить сводку ошибок за период"""
        logger.debug("Анализ ошибок", period_hours=hours)
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            errors = await self._collect_errors(start_time, end_time)
            
            # Группировка ошибок
            error_types = Counter()
            error_modules = Counter()
            error_timeline = defaultdict(int)
            
            for error in errors:
                error_types[error.get("error_type", "unknown")] += 1
                error_modules[error.get("module", "unknown")] += 1
                
                # Группировка по часам
                hour_key = error["timestamp"].strftime("%Y-%m-%d %H:00")
                error_timeline[hour_key] += 1
            
            summary = {
                "period": f"{hours}h",
                "total_errors": len(errors),
                "error_types": dict(error_types.most_common(10)),
                "error_modules": dict(error_modules.most_common(10)),
                "timeline": dict(error_timeline),
                "recent_errors": errors[-10:] if errors else [],
                "timestamp": end_time
            }
            
            logger.info("Анализ ошибок завершен", 
                       total_errors=len(errors),
                       period_hours=hours)
            
            return summary
            
        except Exception as e:
            logger.exception("Ошибка анализа ошибок", error=str(e))
            return {"error": str(e), "timestamp": datetime.now()}
    
    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Получить метрики производительности"""
        logger.debug("Анализ производительности", period_hours=hours)
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            api_metrics = await self._analyze_api_performance(start_time, end_time)
            model_metrics = await self._analyze_model_performance(start_time, end_time)
            system_metrics = await self._analyze_system_performance(start_time, end_time)
            
            metrics = {
                "period": f"{hours}h",
                "api_performance": api_metrics,
                "model_performance": model_metrics,
                "system_performance": system_metrics,
                "timestamp": end_time
            }
            
            logger.info("Анализ производительности завершен", period_hours=hours)
            return metrics
            
        except Exception as e:
            logger.exception("Ошибка анализа производительности", error=str(e))
            return {"error": str(e), "timestamp": datetime.now()}
    
    async def _count_errors(self, start_time: datetime, end_time: datetime) -> int:
        """Подсчет ошибок за период"""
        errors = await self._collect_errors(start_time, end_time)
        return len(errors)
    
    async def _count_warnings(self, start_time: datetime, end_time: datetime) -> int:
        """Подсчет предупреждений за период"""
        warnings = await self._collect_warnings(start_time, end_time)
        return len(warnings)
    
    async def _collect_errors(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Сбор ошибок из логов"""
        errors = []
        
        # Поиск в структурированных логах
        structured_logs = self.logs_dir.glob("*-structured.jsonl")
        
        for log_file in structured_logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get("level") == "error":
                                timestamp = datetime.fromisoformat(entry["timestamp"])
                                if start_time <= timestamp <= end_time:
                                    errors.append({
                                        "timestamp": timestamp,
                                        "message": entry.get("message", ""),
                                        "module": entry.get("logger", "unknown"),
                                        "error_type": self._classify_error(entry.get("message", "")),
                                        "details": entry
                                    })
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception as e:
                logger.warning(f"Ошибка чтения лог файла {log_file}: {e}")
        
        return sorted(errors, key=lambda x: x["timestamp"])
    
    async def _collect_warnings(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Сбор предупреждений из логов"""
        warnings = []
        
        structured_logs = self.logs_dir.glob("*-structured.jsonl")
        
        for log_file in structured_logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get("level") == "warning":
                                timestamp = datetime.fromisoformat(entry["timestamp"])
                                if start_time <= timestamp <= end_time:
                                    warnings.append({
                                        "timestamp": timestamp,
                                        "message": entry.get("message", ""),
                                        "module": entry.get("logger", "unknown"),
                                        "details": entry
                                    })
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception as e:
                logger.warning(f"Ошибка чтения лог файла {log_file}: {e}")
        
        return sorted(warnings, key=lambda x: x["timestamp"])
    
    async def _analyze_api_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Анализ производительности API"""
        api_requests = []
        
        # Поиск API запросов в структурированных логах
        structured_logs = self.logs_dir.glob("*-structured.jsonl")
        
        for log_file in structured_logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if "api_method" in entry and "duration" in entry:
                                timestamp = datetime.fromisoformat(entry["timestamp"])
                                if start_time <= timestamp <= end_time:
                                    api_requests.append(entry)
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception:
                continue
        
        if not api_requests:
            return {"total_requests": 0}
        
        # Анализ метрик
        total_requests = len(api_requests)
        durations = [req.get("duration", 0) for req in api_requests]
        avg_response_time = sum(durations) / len(durations) if durations else 0
        
        # Группировка по endpoints
        endpoints = Counter(req.get("api_path", "unknown") for req in api_requests)
        
        # Группировка по статус кодам
        status_codes = Counter(req.get("status_code", 0) for req in api_requests)
        
        return {
            "total_requests": total_requests,
            "avg_response_time": round(avg_response_time, 3),
            "max_response_time": max(durations) if durations else 0,
            "min_response_time": min(durations) if durations else 0,
            "endpoints": dict(endpoints.most_common(10)),
            "status_codes": dict(status_codes),
            "requests_per_hour": round(total_requests / ((end_time - start_time).total_seconds() / 3600), 2)
        }
    
    async def _analyze_model_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Анализ производительности моделей"""
        model_operations = []
        
        structured_logs = self.logs_dir.glob("*-structured.jsonl")
        
        for log_file in structured_logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if "model_id" in entry and "operation" in entry:
                                timestamp = datetime.fromisoformat(entry["timestamp"])
                                if start_time <= timestamp <= end_time:
                                    model_operations.append(entry)
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception:
                continue
        
        if not model_operations:
            return {"models": {}}
        
        # Анализ по моделям
        models_stats = defaultdict(lambda: {
            "operations": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration": 0,
            "durations": []
        })
        
        for op in model_operations:
            model_id = op.get("model_id", "unknown")
            status = op.get("status", "unknown")
            duration = op.get("duration", 0)
            
            models_stats[model_id]["operations"] += 1
            if status == "success":
                models_stats[model_id]["successful"] += 1
            else:
                models_stats[model_id]["failed"] += 1
            
            if duration:
                models_stats[model_id]["durations"].append(duration)
        
        # Вычисление средних значений
        for model_id, stats in models_stats.items():
            if stats["durations"]:
                stats["avg_duration"] = sum(stats["durations"]) / len(stats["durations"])
            del stats["durations"]  # Удаляем сырые данные
        
        return {
            "models": dict(models_stats),
            "total_operations": len(model_operations),
            "failed_operations": sum(1 for op in model_operations if op.get("status") != "success")
        }
    
    async def _analyze_system_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Анализ системной производительности"""
        # Базовая реализация - можно расширить
        return {
            "uptime_hours": (datetime.now() - start_time).total_seconds() / 3600,
            "log_files_count": len(list(self.logs_dir.glob("*.log"))),
            "structured_logs_count": len(list(self.logs_dir.glob("*.jsonl")))
        }
    
    def _classify_error(self, message: str) -> str:
        """Классификация ошибок по типам"""
        message_lower = message.lower()
        
        if "connection" in message_lower or "timeout" in message_lower:
            return "connection_error"
        elif "model" in message_lower:
            return "model_error"
        elif "api" in message_lower or "http" in message_lower:
            return "api_error"
        elif "config" in message_lower or "setting" in message_lower:
            return "configuration_error"
        elif "file" in message_lower or "path" in message_lower:
            return "file_error"
        else:
            return "general_error"

# Глобальный экземпляр анализатора
log_analyzer = LogAnalyzer()