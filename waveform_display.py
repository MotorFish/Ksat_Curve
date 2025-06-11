#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
气隙磁密波形可视化：原始半周期数据和延拓后的完整周期数据
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_processor import DataProcessor


def plot_waveforms(case_ids=None, save_individual=False):
    """
    绘制指定case的波形
    Args:
        case_ids: 要绘制的case编号列表，None表示绘制所有case
        save_individual: 是否为每个case单独保存图片
    """
    # 处理数据
    processor = DataProcessor()
    processor.process_all_cases(harmonic_filter_n=10)
    
    if not processor.get_all_cases():
        print("没有找到有效的case数据")
        return
    
    # 如果没有指定case_ids，则绘制所有case
    if case_ids is None:
        case_ids = sorted([int(case_id) for case_id in processor.cases.keys()])
    
    # 设置中文字体（如果需要）
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    
    for case_id in case_ids:
        case_data = processor.get_case_data(str(case_id))
        if case_data is None or case_data.airgap_flux_data is None:
            print(f"Case {case_id} 数据不完整，跳过")
            continue
        
        # 提取原始数据
        original_data = case_data.airgap_flux_data['Bn'].values  # 保留完整原始序列
        length_data = case_data.airgap_flux_data['length'].values
        
        # 获取完整周期数据
        full_cycle_data = case_data.full_cycle_flux
        
        # 为完整周期创建对应的长度坐标
        # 原始数据对应0到某个长度L，延拓数据从第二个点开始
        max_length = length_data[-1]
        # 延拓部分的长度坐标：从原数据第二个点到倒数第二个点，加上偏移量
        n_points = len(length_data)
        extension_length = length_data[1:n_points-1] + max_length  # 从第二个点到倒数第二个点的长度坐标
        full_cycle_length = np.concatenate([
            length_data,  # 原始数据
            extension_length  # 延拓数据（从第二个点到倒数第二个点）
        ])
        
        # 创建图表
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 14))
        
        # 子图1：原始半周期数据
        ax1.plot(length_data, original_data, 'b-', linewidth=2, label='Original Half Cycle')
        ax1.set_title(f'Case {case_id} - Original Half Cycle Data')
        ax1.set_xlabel('Length (mm)')
        ax1.set_ylabel('Magnetic Flux Density (T)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 子图2：延拓后的完整周期数据
        ax2.plot(full_cycle_length, full_cycle_data, 'r-', linewidth=2, label='Extended Full Cycle')
        # 标记分界点
        ax2.axvline(x=max_length, color='k', linestyle='--', alpha=0.7, label='Mirror Point')
        ax2.set_title(f'Case {case_id} - Extended Full Cycle Data')
        ax2.set_xlabel('Length (mm)')
        ax2.set_ylabel('Magnetic Flux Density (T)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # 子图3：滤波后的完整周期数据
        if case_data.filtered_signal is not None:
            ax3.plot(full_cycle_length, case_data.filtered_signal, 'g-', linewidth=2, label='Filtered Signal')
            ax3.axvline(x=max_length, color='k', linestyle='--', alpha=0.7, label='Mirror Point')
            ax3.set_title(f'Case {case_id} - Filtered Signal')
            ax3.set_xlabel('Length (mm)')
            ax3.set_ylabel('Magnetic Flux Density (T)')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
        
        # 子图4：重叠对比
        ax4.plot(length_data, original_data, 'b-', linewidth=2, label='Original Half Cycle')
        ax4.plot(full_cycle_length, full_cycle_data, 'r-', linewidth=1.5, alpha=0.7, label='Extended Full Cycle')
        if case_data.filtered_signal is not None:
            ax4.plot(full_cycle_length, case_data.filtered_signal, 'g-', linewidth=1.5, alpha=0.8, label='Filtered Signal')
        ax4.axvline(x=max_length, color='k', linestyle='--', alpha=0.7, label='Mirror Point')
        ax4.set_title(f'Case {case_id} - All Signals Comparison')
        ax4.set_xlabel('Length (mm)')
        ax4.set_ylabel('Magnetic Flux Density (T)')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        # 添加整体信息
        info_text = f'Ksat: {case_data.ksat:.3f}, alpha_i: {case_data.alpha_i:.3f}, K_Nm: {case_data.k_nm:.3f}'
        fig.suptitle(f'Case {case_id} Waveform Analysis\n{info_text}', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存图片到统一输出文件夹
        if save_individual:
            import os
            output_dir = "output_results"
            os.makedirs(output_dir, exist_ok=True)
            filename = f'waveform_case_{case_id}.png'
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"已保存: {filepath}")
        
        plt.show()

if __name__ == "__main__":
    print("生成波形可视化...")
    
    # 绘制几个代表性case的详细波形
    plot_waveforms(case_ids=[8], save_individual=True)
    
    print("波形可视化完成！") 