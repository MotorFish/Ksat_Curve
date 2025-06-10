import os
import pandas as pd
import glob
import re
import numpy as np
from typing import Dict, List, Optional


class CaseData:
    """存储每个case数据的类"""
    
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.hm_delta: Optional[float] = None
        self.hm_dr: Optional[float] = None
        self.hm_ds: Optional[float] = None
        self.airgap_flux_data: Optional[pd.DataFrame] = None
        
        # 计算得出的数据
        self.ksat: Optional[float] = None  # 饱和系数
        self.b_av: Optional[float] = None  # 完整周期绝对值平均值
        self.b_delta1: Optional[float] = None  # FFT基波幅值
        self.b_delta: Optional[float] = None  # 滤波后幅值
        self.full_cycle_flux: Optional[np.ndarray] = None  # 完整周期数据
        self.filtered_signal: Optional[np.ndarray] = None  # 滤波后的信号
        self.alpha_i: Optional[float] = None  # alpha_i = B_av/B_delta
        self.k_nm: Optional[float] = None  # K_Nm = 1/sqrt(2) * (B_delta1/B_av)
        
    def calculate_ksat(self):
        """计算饱和系数 Ksat=1+(Hm_dr*23.6+Hm_ds*27)/(Hm_delta*0.4)"""
        if all(v is not None for v in [self.hm_delta, self.hm_dr, self.hm_ds]):
            if self.hm_delta != 0:
                self.ksat = 1 + (self.hm_dr * 23.6 + self.hm_ds * 27) / (self.hm_delta * 0.4)
            else:
                self.ksat = None
        else:
            self.ksat = None
    
    def calculate_ratios(self):
        """计算alpha_i和K_Nm比值"""
        # 计算 alpha_i = B_av/B_delta
        if self.b_av is not None and self.b_delta is not None and self.b_delta != 0:
            self.alpha_i = self.b_av / self.b_delta
        else:
            self.alpha_i = None
        
        # 计算 K_Nm = 1/sqrt(2) * (B_delta1/B_av)
        if self.b_delta1 is not None and self.b_av is not None and self.b_av != 0:
            self.k_nm = (1 / np.sqrt(2)) * (self.b_delta1 / self.b_av)
        else:
            self.k_nm = None
    
    def process_airgap_flux(self, harmonic_filter_n: int = 50):
        """
        处理气隙磁密数据，并计算Hm_delta
        Args:
            harmonic_filter_n: 谐波滤波次数，保留小于n次的谐波
        """
        if self.airgap_flux_data is None:
            return
        
        try:
            # 真空磁导率 μ₀ = 4π × 10⁻⁷ H/m
            mu_0 = 4 * np.pi * 1e-7
            
            # 提取磁密数据（保留完整原始序列）
            bn_data = self.airgap_flux_data['Bn'].values  # 保留所有数据点
            
            # 构造完整周期数据（通过解析延拓）
            # 从原数据的第二行到倒数第二行，取反后接到原数据末尾
            # 避免在延拓点处重复第一个点和最后一个点
            n_points = len(bn_data)  # 获取原序列采样点数
            extension_data = -bn_data[1:n_points-1]  # 从第二行(索引1)到倒数第二行，取反
            bn_full_cycle = np.concatenate([bn_data, extension_data])
            
            self.full_cycle_flux = bn_full_cycle
            
            # 1. 计算完整周期的绝对值平均值
            self.b_av = np.mean(np.abs(bn_full_cycle))
            
            # 2. FFT分析
            fft_result = np.fft.fft(bn_full_cycle)
            n_points = len(bn_full_cycle)
            
            # 基波幅值（第1次谐波）
            self.b_delta1 = 2 * np.abs(fft_result[1]) / n_points
            
            # 3. 谐波滤波：保留0到n次谐波
            fft_filtered = fft_result.copy()
            # 清除高次谐波，保留0到harmonic_filter_n次谐波
            if harmonic_filter_n < n_points // 2:
                # 清除正频部分的高次谐波（保留0到harmonic_filter_n）
                fft_filtered[harmonic_filter_n+1:n_points//2] = 0
                # 清除负频部分的高次谐波（对称清除）
                fft_filtered[n_points//2+1:n_points-harmonic_filter_n] = 0
            
            # 反变换得到滤波后的信号
            filtered_signal = np.fft.ifft(fft_filtered).real
            self.filtered_signal = filtered_signal  # 保存滤波后的信号
            
            # 计算滤波后的幅值（可以用RMS值或最大值）
            self.b_delta = np.max(np.abs(filtered_signal))  # 取滤波后信号的最大绝对值作为幅值
            
            # 4. 计算Hm_delta = 滤波后磁密最大值 / 真空磁导率
            b_max_filtered = np.max(np.abs(filtered_signal))
            self.hm_delta = b_max_filtered / mu_0
            
        except Exception as e:
            self.b_av = None
            self.b_delta1 = None
            self.b_delta = None
            self.full_cycle_flux = None
            self.filtered_signal = None
            self.hm_delta = None
            self.alpha_i = None
            self.k_nm = None
    
    def __str__(self):
        flux_info = f"airgap_flux_rows={len(self.airgap_flux_data) if self.airgap_flux_data is not None else 0}"
        ksat_info = f"Ksat={self.ksat:.4f}" if self.ksat is not None else "Ksat=None"
        return f"Case {self.case_id}: Hm_delta={self.hm_delta}, Hm_dr={self.hm_dr}, Hm_ds={self.hm_ds}, {ksat_info}, {flux_info}"
    
    def __repr__(self):
        return self.__str__()


class DataProcessor:
    """处理prmtric.1目录中所有case数据的主类"""
    
    def __init__(self, base_dir: str = "prmtric.1"):
        self.base_dir = base_dir
        self.cases: Dict[str, CaseData] = {}
        
    def get_case_directories(self) -> List[str]:
        """获取所有case目录"""
        case_pattern = os.path.join(self.base_dir, "case.*")
        case_dirs = glob.glob(case_pattern)
        # 提取case编号并排序
        case_nums = []
        for case_dir in case_dirs:
            case_name = os.path.basename(case_dir)
            if case_name.startswith("case."):
                try:
                    case_num = int(case_name.split(".")[1])
                    case_nums.append((case_num, case_dir))
                except ValueError:
                    pass
        
        # 按case编号排序
        case_nums.sort(key=lambda x: x[0])
        return [case_dir for _, case_dir in case_nums]
    
    def parse_output_txt(self, output_file: str) -> tuple:
        """解析output.txt文件，提取Hm_dr和Hm_ds参数值"""
        hm_dr, hm_ds = None, None
        
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 使用正则表达式提取参数值
            hm_dr_match = re.search(r'Hm_dr\s*=\s*([\d.-]+)', content)
            hm_ds_match = re.search(r'Hm_ds\s*=\s*([\d.-]+)', content)
            
            if hm_dr_match:
                hm_dr = float(hm_dr_match.group(1))
            if hm_ds_match:
                hm_ds = float(hm_ds_match.group(1))
                
        except Exception as e:
            pass
            
        return hm_dr, hm_ds
    
    def read_airgap_flux_csv(self, csv_file: str) -> Optional[pd.DataFrame]:
        """读取airgapflux.csv文件中的气隙磁密数据"""
        try:
            df = pd.read_csv(csv_file)
            return df
        except Exception as e:
            return None
    
    def process_single_case(self, case_dir: str, harmonic_filter_n: int = 1) -> Optional[CaseData]:
        """处理单个case目录"""
        case_name = os.path.basename(case_dir)
        case_id = case_name.split(".")[1] if "." in case_name else case_name
        
        # 创建case数据实例
        case_data = CaseData(case_id)
        
        # 构建文件路径
        output_file = os.path.join(case_dir, "output.txt")
        airgap_file = os.path.join(case_dir, "airgapflux.csv")
        
        # 检查必要文件是否存在
        if not os.path.exists(output_file) or not os.path.exists(airgap_file):
            return None
        
        # 解析output.txt文件
        case_data.hm_dr, case_data.hm_ds = self.parse_output_txt(output_file)
        
        # 读取airgapflux.csv文件
        case_data.airgap_flux_data = self.read_airgap_flux_csv(airgap_file)
        
        # 处理气隙磁密数据（会计算Hm_delta）
        case_data.process_airgap_flux(harmonic_filter_n)
        
        # 计算饱和系数
        case_data.calculate_ksat()
        
        # 计算比值
        case_data.calculate_ratios()
        
        return case_data
    
    def process_all_cases(self, harmonic_filter_n: int = 50):
        """处理所有case目录"""
        case_dirs = self.get_case_directories()
        
        if not case_dirs:
            return
        

        
        for case_dir in case_dirs:
            case_data = self.process_single_case(case_dir, harmonic_filter_n)
            if case_data:
                self.cases[case_data.case_id] = case_data
    
    def get_case_data(self, case_id: str) -> Optional[CaseData]:
        """获取指定case的数据"""
        return self.cases.get(case_id)
    
    def get_all_cases(self) -> Dict[str, CaseData]:
        """获取所有case数据"""
        return self.cases
    
    def get_case_summary(self) -> pd.DataFrame:
        """获取所有case的核心计算结果"""
        summary_data = []
        for case_id, case_data in self.cases.items():
            summary_data.append({
                'case_id': case_data.case_id,
                'hm_delta': case_data.hm_delta,
                'hm_dr': case_data.hm_dr,
                'hm_ds': case_data.hm_ds,
                'ksat': case_data.ksat,
                'b_av': case_data.b_av,
                'b_delta1': case_data.b_delta1,
                'b_delta': case_data.b_delta,
                'alpha_i': case_data.alpha_i,
                'k_nm': case_data.k_nm
            })
        
        return pd.DataFrame(summary_data)
    
    def save_to_csv(self, filename: str = "calculated_results.csv"):
        """将所有数据保存为CSV文件"""
        df = self.get_case_summary()
        # 按case_id排序
        df['case_id_num'] = df['case_id'].astype(int)
        df = df.sort_values('case_id_num').drop('case_id_num', axis=1)
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        return filename


if __name__ == "__main__":
    # 核心功能测试
    processor = DataProcessor()
    processor.process_all_cases(harmonic_filter_n=1)  # 设置滤波截止频率为1（只保留基波）
    
    # 保存为CSV文件
    csv_file = processor.save_to_csv()
    print(f"处理了 {len(processor.cases)} 个case，已保存到 {csv_file}") 