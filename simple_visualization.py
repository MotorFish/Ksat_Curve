#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版可视化：Ksat与磁密比值的关系（使用英文标签）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_processor import DataProcessor


def create_visualization():
    """创建双y轴可视化图表"""
    # 加载数据
    processor = DataProcessor()
    processor.process_all_cases(harmonic_filter_n=5)
    
    if not processor.get_all_cases():
        return
    
    # 获取摘要数据
    summary_df = processor.get_case_summary()
    
    # 过滤有效数据并按Ksat排序
    valid_data = summary_df[summary_df['ksat'].notna() & 
                           summary_df['alpha_i'].notna() & 
                           summary_df['k_nm'].notna()].copy()
    valid_data = valid_data.sort_values('ksat')
    
    # 创建双y轴图表
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # 第一个y轴：alpha_i
    color1 = 'tab:blue'
    ax1.set_xlabel('Saturation Coefficient Ksat', fontsize=12)
    ax1.set_ylabel('alpha_i (B_av / B_delta)', color=color1, fontsize=12)
    line1 = ax1.plot(valid_data['ksat'], valid_data['alpha_i'], 
                     'o-', color=color1, linewidth=2, markersize=6, label='alpha_i')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # 第二个y轴：K_Nm
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('K_Nm (1/sqrt(2) * B_delta1/B_av)', color=color2, fontsize=12)
    line2 = ax2.plot(valid_data['ksat'], valid_data['k_nm'], 
                     's-', color=color2, linewidth=2, markersize=6, label='K_Nm')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 添加标题和图例
    plt.title('Ksat vs alpha_i and K_Nm', fontsize=14, fontweight='bold')
    
    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig('ksat_alpha_knm.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return valid_data


if __name__ == "__main__":
    create_visualization() 