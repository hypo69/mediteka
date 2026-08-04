# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Визуализация результатов нагрузочного тестирования
# =============================================================================
# Описание:
#   Читает CSV файлы, сгенерированные Locust, и строит графики 
#   распределения времени ответа и количества запросов в секунду (RPS).
#
# Использование:
#   python tests/visualize_performance.py
#
# File: tests/visualize_performance.py
# Project: Ai Assistant
# Author: Gemini Code Assist
# =============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

def generate_performance_charts():
    # Определение путей к отчетам
    report_dir = Path(__file__).parent / "reports" / "load"
    stats_history_file = report_dir / "locust_results_stats_history.csv"
    output_plot = report_dir / "performance_dashboard.png"

    if not stats_history_file.exists():
        print(f"❌ Файл истории статистики не найден: {stats_history_file}")
        print("Сначала запустите нагрузочные тесты через run-load-tests.ps1")
        return

    print(f"📊 Чтение данных из {stats_history_file}...")
    df = pd.read_csv(stats_history_file)

    # Преобразование меток времени (если есть) или использование индексов
    df['Elapsed Seconds'] = range(len(df))

    # Настройка графиков
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    plt.subplots_adjust(hspace=0.4)

    # График 1: Время ответа (Response Times)
    ax1.set_title('Response Times (ms)', fontsize=14, fontweight='bold')
    ax1.plot(df['Elapsed Seconds'], df['Total Average Response Time'], label='Average', color='blue', linewidth=2)
    ax1.plot(df['Elapsed Seconds'], df['Total Min Response Time'], label='Min', color='green', linestyle='--')
    ax1.plot(df['Elapsed Seconds'], df['Total Max Response Time'], label='Max', color='red', linestyle=':')
    ax1.set_ylabel('Milliseconds')
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)
    ax1.legend()

    # График 2: Пропускная способность (RPS) и Ошибки
    ax2.set_title('Throughput & Errors', fontsize=14, fontweight='bold')
    ax2.plot(df['Elapsed Seconds'], df['Requests/s'], label='Requests per Second', color='purple', linewidth=2)
    
    # Создаем вторую ось Y для ошибок
    ax2_err = ax2.twinx()
    ax2_err.fill_between(df['Elapsed Seconds'], df['Failures/s'], color='red', alpha=0.3, label='Failures/s')
    ax2_err.set_ylabel('Failures per Second', color='red')
    ax2_err.tick_params(axis='y', labelcolor='red')

    ax2.set_xlabel('Seconds since start')
    ax2.set_ylabel('Requests per Second', color='purple')
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # Сбор легенд для второй оси
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_err.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    # Сохранение результата
    plt.savefig(output_plot)
    print(f"✅ Графики успешно сохранены: {output_plot}")

if __name__ == "__main__":
    # Установка стиля (опционально)
    plt.style.use('ggplot')
    generate_performance_charts()