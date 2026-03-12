"""
FaunaFuck 日志分析器
分析细胞种群演化数据，生成可视化报告
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import matplotlib
from collections import defaultdict
from datetime import datetime

matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


@dataclass
class FrameData:
    """单帧数据"""
    tick: int
    total_cells: int
    dna_diversity: int  # DNA种类数
    rna_diversity: int  # RNA种类数
    dna_sequences: List[Tuple[str, int, int]]  # (序列, 数量, 长度)
    rna_sequences: List[Tuple[str, int, int]]  # (序列, 数量, 长度)
    dominant_dna: str  # 主导DNA
    dominant_dna_count: int
    dominant_dna_length: int


class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.frames: List[FrameData] = []
        
    def find_log_files(self) -> List[Path]:
        """查找所有日志文件，按时间排序"""
        log_files = list(self.log_dir.glob("fauna_*.log"))
        # 按文件名中的时间戳排序
        log_files.sort(key=lambda p: p.stem.split('_', 1)[1] if '_' in p.stem else '')
        return log_files
    
    def parse_frame(self, text: str) -> FrameData:
        """解析单帧数据"""
        # 提取帧数
        tick_match = re.search(r'当前帧数: (\d+)', text)
        tick = int(tick_match.group(1)) if tick_match else 0
        
        # 提取DNA统计
        dna_match = re.search(r'收集到 (\d+) 种不同的DNA，共 (\d+) 个细胞', text)
        dna_diversity = int(dna_match.group(1)) if dna_match else 0
        total_cells = int(dna_match.group(2)) if dna_match else 0
        
        # 提取RNA统计
        rna_match = re.search(r'收集到 (\d+) 种不同的RNA', text)
        rna_diversity = int(rna_match.group(1)) if rna_match else 0
        
        # 提取DNA序列（只取前3名）
        dna_sequences = []
        dna_section = re.search(r'=== 收集到.*?DNA.*?===\n(.*?)(?:===|$)', text, re.DOTALL)
        if dna_section:
            lines = dna_section.group(1).strip().split('\n')[:3]
            for line in lines:
                match = re.search(r'x\s*(\d+)\s+\|\s+len=\s*(\d+)\s+\|\s+(.+)$', line)
                if match:
                    count = int(match.group(1))
                    length = int(match.group(2))
                    sequence = match.group(3).strip()
                    dna_sequences.append((sequence, count, length))
        
        # 提取RNA序列（只取前3名）
        rna_sequences = []
        rna_section = re.search(r'=== 收集到.*?RNA.*?===\n(.*?)(?:$)', text, re.DOTALL)
        if rna_section:
            lines = rna_section.group(1).strip().split('\n')[:3]
            for line in lines:
                match = re.search(r'x\s*(\d+)\s+\|\s+len=\s*(\d+)\s+\|\s+(.+)$', line)
                if match:
                    count = int(match.group(1))
                    length = int(match.group(2))
                    sequence = match.group(3).strip()
                    rna_sequences.append((sequence, count, length))
        
        # 主导种群数据
        dominant_dna = dna_sequences[0][0] if dna_sequences else ""
        dominant_dna_count = dna_sequences[0][1] if dna_sequences else 0
        dominant_dna_length = dna_sequences[0][2] if dna_sequences else 0
        
        return FrameData(
            tick=tick,
            total_cells=total_cells,
            dna_diversity=dna_diversity,
            rna_diversity=rna_diversity,
            dna_sequences=dna_sequences,
            rna_sequences=rna_sequences,
            dominant_dna=dominant_dna,
            dominant_dna_count=dominant_dna_count,
            dominant_dna_length=dominant_dna_length
        )
    
    def load_logs(self):
        """加载所有日志文件"""
        log_files = self.find_log_files()
        print(f"找到 {len(log_files)} 个日志文件")
        
        for log_file in log_files:
            print(f"解析: {log_file.name}")
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 按帧分割
            frame_blocks = re.split(r'=== 当前帧数:', content)
            for block in frame_blocks[1:]:  # 跳过第一个空块
                block = '=== 当前帧数:' + block
                try:
                    frame_data = self.parse_frame(block)
                    if frame_data.tick > 0:
                        self.frames.append(frame_data)
                except Exception as e:
                    print(f"解析帧数据时出错: {e}")
                    continue
        
        # 按tick排序
        self.frames.sort(key=lambda f: f.tick)
        print(f"共解析 {len(self.frames)} 帧数据")
    
    def plot_population_dynamics(self):
        """绘制种群动态"""
        if not self.frames:
            print("没有数据可绘制")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('FaunaFuck 细胞种群演化分析', fontsize=16, fontweight='bold')
        
        ticks = [f.tick for f in self.frames]
        
        # 1. 总细胞数变化
        ax = axes[0, 0]
        total_cells = [f.total_cells for f in self.frames]
        ax.plot(ticks, total_cells, 'b-', linewidth=2)
        ax.fill_between(ticks, total_cells, alpha=0.3)
        ax.set_xlabel('Tick (帧数)')
        ax.set_ylabel('细胞总数')
        ax.set_title('种群规模变化')
        ax.grid(True, alpha=0.3)
        
        # 2. 多样性变化
        ax = axes[0, 1]
        dna_diversity = [f.dna_diversity for f in self.frames]
        rna_diversity = [f.rna_diversity for f in self.frames]
        ax.plot(ticks, dna_diversity, 'r-', label='DNA多样性', linewidth=2)
        ax.plot(ticks, rna_diversity, 'g-', label='RNA多样性', linewidth=2)
        ax.set_xlabel('Tick (帧数)')
        ax.set_ylabel('种类数量')
        ax.set_title('遗传多样性变化')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 3. 主导种群占比
        ax = axes[1, 0]
        dominant_ratio = [f.dominant_dna_count / f.total_cells * 100 
                         if f.total_cells > 0 else 0 
                         for f in self.frames]
        ax.plot(ticks, dominant_ratio, 'purple', linewidth=2)
        ax.fill_between(ticks, dominant_ratio, alpha=0.3, color='purple')
        ax.set_xlabel('Tick (帧数)')
        ax.set_ylabel('占比 (%)')
        ax.set_title('主导DNA种群占比')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        
        # 4. 主导DNA长度变化
        ax = axes[1, 1]
        dominant_length = [f.dominant_dna_length for f in self.frames]
        ax.plot(ticks, dominant_length, 'orange', linewidth=2, marker='o', markersize=3)
        ax.set_xlabel('Tick (帧数)')
        ax.set_ylabel('碱基对长度')
        ax.set_title('主导DNA序列长度演化')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        output_file = self.log_dir / f"evolution_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n图表已保存到: {output_file}")
        
        plt.show()
    
    def generate_report(self):
        """生成文本报告"""
        if not self.frames:
            print("没有数据可分析")
            return
        
        first_frame = self.frames[0]
        last_frame = self.frames[-1]
        
        print("\n" + "="*60)
        print("FaunaFuck 演化分析报告")
        print("="*60)
        
        print(f"\n📊 基本统计:")
        print(f"  分析帧数: {first_frame.tick} -> {last_frame.tick} ({len(self.frames)} 个数据点)")
        print(f"  初始种群: {first_frame.total_cells} 个细胞")
        print(f"  最终种群: {last_frame.total_cells} 个细胞")
        print(f"  种群变化: {last_frame.total_cells - first_frame.total_cells:+d} ({(last_frame.total_cells/first_frame.total_cells - 1)*100:+.1f}%)")
        
        print(f"\n🧬 遗传多样性:")
        print(f"  初始DNA种类: {first_frame.dna_diversity}")
        print(f"  最终DNA种类: {last_frame.dna_diversity}")
        print(f"  初始RNA种类: {first_frame.rna_diversity}")
        print(f"  最终RNA种类: {last_frame.rna_diversity}")
        
        # 计算平均多样性
        avg_dna_diversity = sum(f.dna_diversity for f in self.frames) / len(self.frames)
        avg_rna_diversity = sum(f.rna_diversity for f in self.frames) / len(self.frames)
        print(f"  平均DNA种类: {avg_dna_diversity:.1f}")
        print(f"  平均RNA种类: {avg_rna_diversity:.1f}")
        
        print(f"\n👑 主导种群:")
        print(f"  初始主导DNA: {first_frame.dominant_dna[:30]}... (长度: {first_frame.dominant_dna_length})")
        print(f"  初始主导占比: {first_frame.dominant_dna_count/first_frame.total_cells*100:.1f}%")
        print(f"  最终主导DNA: {last_frame.dominant_dna[:30]}... (长度: {last_frame.dominant_dna_length})")
        print(f"  最终主导占比: {last_frame.dominant_dna_count/last_frame.total_cells*100:.1f}%")
        
        # 找出种群数量的峰值和谷值
        max_pop_frame = max(self.frames, key=lambda f: f.total_cells)
        min_pop_frame = min(self.frames, key=lambda f: f.total_cells)
        
        print(f"\n📈 种群波动:")
        print(f"  最大种群: {max_pop_frame.total_cells} (tick {max_pop_frame.tick})")
        print(f"  最小种群: {min_pop_frame.total_cells} (tick {min_pop_frame.tick})")
        print(f"  波动范围: {max_pop_frame.total_cells - min_pop_frame.total_cells}")
        
        # 检测演化趋势
        if len(self.frames) > 10:
            mid_point = len(self.frames) // 2
            early_avg = sum(f.total_cells for f in self.frames[:mid_point]) / mid_point
            late_avg = sum(f.total_cells for f in self.frames[mid_point:]) / (len(self.frames) - mid_point)
            
            print(f"\n🔄 演化趋势:")
            if late_avg > early_avg * 1.1:
                print(f"  种群呈增长趋势 (前半段平均: {early_avg:.0f}, 后半段平均: {late_avg:.0f})")
            elif late_avg < early_avg * 0.9:
                print(f"  种群呈下降趋势 (前半段平均: {early_avg:.0f}, 后半段平均: {late_avg:.0f})")
            else:
                print(f"  种群保持稳定 (前半段平均: {early_avg:.0f}, 后半段平均: {late_avg:.0f})")
        
        print("\n" + "="*60 + "\n")


def main():
    """主函数"""
    analyzer = LogAnalyzer("logs")
    
    print("开始加载日志文件...")
    analyzer.load_logs()
    
    if analyzer.frames:
        print("\n生成分析报告...")
        analyzer.generate_report()
        
        print("\n生成可视化图表...")
        analyzer.plot_population_dynamics()
    else:
        print("未找到有效的日志数据")


if __name__ == "__main__":
    main()
