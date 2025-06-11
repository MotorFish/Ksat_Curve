#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一可视化脚本：合并comprehensive_visualization和formatted_table_output功能
输出K_W曲线和Ksat对alpha_i、K_Nm、K_W的表格
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_processor import DataProcessor
import matplotlib
import os

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 统一输出文件夹
OUTPUT_DIR = "output_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_visualization():
    """创建可视化图表和数据表格"""
    # 加载数据
    processor = DataProcessor()
    processor.process_all_cases(harmonic_filter_n=5)
    
    if not processor.get_all_cases():
        print("没有找到有效的数据")
        return
    
    # 获取摘要数据
    summary_df = processor.get_case_summary()
    
    # 过滤有效数据并按Ksat排序
    valid_data = summary_df[summary_df['ksat'].notna() & 
                           summary_df['alpha_i'].notna() & 
                           summary_df['k_nm'].notna() &
                           summary_df['k_w'].notna()].copy()
    valid_data = valid_data.sort_values('ksat')
    
    # 1. 创建综合图表（包含K_W）
    create_comprehensive_plot(valid_data)
    
    # 2. 创建K_W单独曲线图
    create_kw_plot(valid_data)
    
    # 3. 创建原有的alpha_i和K_Nm图表
    create_alpha_knm_plot(valid_data)
    
    # 4. 输出数据表格
    create_data_table(valid_data)
    
    print(f"所有结果已保存到文件夹: {OUTPUT_DIR}")
    return valid_data


def create_comprehensive_plot(valid_data):
    """创建包含K_W的综合图表"""
    fig, ax1 = plt.subplots(figsize=(14, 10))
    
    # 第一个y轴：alpha_i
    color1 = 'tab:blue'
    ax1.set_xlabel('饱和系数 Ksat', fontsize=14)
    ax1.set_ylabel('alpha_i (B_av / B_delta)', color=color1, fontsize=14)
    ax1.plot(valid_data['ksat'], valid_data['alpha_i'], 
             'o-', color=color1, linewidth=2, markersize=6, label='alpha_i')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # 第二个y轴：K_Nm
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('K_Nm (1/√2 × B_delta1/B_av)', color=color2, fontsize=14)
    ax2.plot(valid_data['ksat'], valid_data['k_nm'], 
             's-', color=color2, linewidth=2, markersize=6, label='K_Nm')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 第三个y轴：K_W
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))
    color3 = 'tab:green'
    ax3.set_ylabel('K_W (B_delta / B_delta1)', color=color3, fontsize=14)
    ax3.plot(valid_data['ksat'], valid_data['k_w'], 
             '^-', color=color3, linewidth=2, markersize=6, label='K_W')
    ax3.tick_params(axis='y', labelcolor=color3)
    
    # 添加标题和图例
    plt.title('饱和系数 Ksat 与磁密比值关系', fontsize=16, fontweight='bold', pad=20)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'ksat_comprehensive.png'), dpi=300, bbox_inches='tight')
    plt.close()


def create_kw_plot(valid_data):
    """创建K_W单独的图表"""
    plt.figure(figsize=(12, 8))
    plt.plot(valid_data['ksat'], valid_data['k_w'], 
             'o-', color='tab:green', linewidth=2, markersize=6, label='K_W = B_delta/B_delta1')
    
    plt.xlabel('饱和系数 Ksat', fontsize=14)
    plt.ylabel('K_W (B_delta / B_delta1)', fontsize=14)
    plt.title('饱和系数 Ksat 与 K_W 的关系', fontsize=16, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'ksat_kw_curve.png'), dpi=300, bbox_inches='tight')
    plt.close()


def create_alpha_knm_plot(valid_data):
    """创建原有的alpha_i和K_Nm双轴图表"""
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # 第一个y轴：alpha_i
    color1 = 'tab:blue'
    ax1.set_xlabel('饱和系数 Ksat', fontsize=14)
    ax1.set_ylabel('alpha_i (B_av / B_delta)', color=color1, fontsize=14)
    ax1.plot(valid_data['ksat'], valid_data['alpha_i'], 
             'o-', color=color1, linewidth=2, markersize=6, label='alpha_i')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # 第二个y轴：K_Nm
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('K_Nm (1/√2 × B_delta1/B_av)', color=color2, fontsize=14)
    ax2.plot(valid_data['ksat'], valid_data['k_nm'], 
             's-', color=color2, linewidth=2, markersize=6, label='K_Nm')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 添加标题和图例
    plt.title('饱和系数 Ksat 与 alpha_i、K_Nm 的关系', fontsize=16, fontweight='bold')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'ksat_alpha_knm.png'), dpi=300, bbox_inches='tight')
    plt.close()


def create_data_table(valid_data):
    """输出Ksat对alpha_i、K_Nm、K_W的表格"""
    # 1. 基础数据表格（主要结果）
    table_data = valid_data[['case_id', 'ksat', 'alpha_i', 'k_nm', 'k_w']].copy()
    
    # 输出表格到控制台
    print("\n" + "="*80)
    print("Ksat 对 alpha_i、K_Nm、K_W 的数据表格")
    print("="*80)
    
    pd.set_option('display.precision', 6)
    pd.set_option('display.width', None)
    pd.set_option('display.max_columns', None)
    
    print(table_data.to_string(index=False))
    
    # 保存基础表格到CSV文件
    table_data.to_csv(os.path.join(OUTPUT_DIR, 'ksat_ratios_table.csv'), 
                      index=False, encoding='utf-8-sig')
    print(f"\n数据表格已保存到: {os.path.join(OUTPUT_DIR, 'ksat_ratios_table.csv')}")
    
    # 2. 完整计算数据表格（包含所有中间计算结果）
    complete_data = valid_data[['case_id', 'hm_delta', 'hm_dr', 'hm_ds', 'ksat', 
                               'b_av', 'b_delta1', 'b_delta', 'alpha_i', 'k_nm', 'k_w']].copy()
    
    # 保存完整数据表格到CSV文件
    complete_data.to_csv(os.path.join(OUTPUT_DIR, 'complete_calculation_results.csv'), 
                        index=False, encoding='utf-8-sig')
    print(f"完整计算数据已保存到: {os.path.join(OUTPUT_DIR, 'complete_calculation_results.csv')}")


if __name__ == "__main__":
    print("创建统一可视化...")
    create_visualization()
    print("完成！") 