"""
FaunaFuck 演化动画生成器
生成DNA/RNA种群演化的动态可视化动画
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
from collections import defaultdict
from datetime import datetime
import numpy as np
from tqdm import tqdm

matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


@dataclass
class FrameData:
    """单帧数据"""
    tick: int
    total_cells: int
    dna_diversity: int
    rna_diversity: int
    dna_sequences: List[Tuple[str, int, int]]  # (序列, 数量, 长度)
    rna_sequences: List[Tuple[str, int, int]]
    top_dna_counts: Dict[str, int]  # 前N名DNA的数量
    top_rna_counts: Dict[str, int]  # 前N名RNA的数量


class AnimationGenerator:
    """动画生成器"""
    
    def __init__(self, log_dir: str = "logs", top_n: int = 10):
        self.log_dir = Path(log_dir)
        self.frames: List[FrameData] = []
        self.top_n = top_n  # 追踪前N名序列
        self.dna_color_map = {}  # DNA序列到颜色的映射
        self.rna_color_map = {}
        self.colors = plt.cm.tab20(np.linspace(0, 1, 20))
        
    def find_log_files(self) -> List[Path]:
        """查找所有日志文件，按时间排序"""
        log_files = list(self.log_dir.glob("fauna_*.log"))
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
        
        # 提取DNA序列（前top_n名）
        dna_sequences = []
        top_dna_counts = {}
        dna_section = re.search(r'=== 收集到.*?DNA.*?===\n(.*?)(?:===|$)', text, re.DOTALL)
        if dna_section:
            lines = dna_section.group(1).strip().split('\n')
            for i, line in enumerate(lines[:self.top_n]):
                match = re.search(r'x\s*(\d+)\s+\|\s+len=\s*(\d+)\s+\|\s+(.+)$', line)
                if match:
                    count = int(match.group(1))
                    length = int(match.group(2))
                    sequence = match.group(3).strip()
                    dna_sequences.append((sequence, count, length))
                    # 用简短标识符（序列前8个字符 + 排名）
                    seq_id = f"#{i+1} {sequence[:8]}..."
                    top_dna_counts[seq_id] = count
        
        # 提取RNA序列（前top_n名）
        rna_sequences = []
        top_rna_counts = {}
        rna_section = re.search(r'=== 收集到.*?RNA.*?===\n(.*?)(?:$)', text, re.DOTALL)
        if rna_section:
            lines = rna_section.group(1).strip().split('\n')
            for i, line in enumerate(lines[:self.top_n]):
                match = re.search(r'x\s*(\d+)\s+\|\s+len=\s*(\d+)\s+\|\s+(.+)$', line)
                if match:
                    count = int(match.group(1))
                    length = int(match.group(2))
                    sequence = match.group(3).strip()
                    rna_sequences.append((sequence, count, length))
                    seq_id = f"#{i+1} {sequence[:12]}..."
                    top_rna_counts[seq_id] = count
        
        return FrameData(
            tick=tick,
            total_cells=total_cells,
            dna_diversity=dna_diversity,
            rna_diversity=rna_diversity,
            dna_sequences=dna_sequences,
            rna_sequences=rna_sequences,
            top_dna_counts=top_dna_counts,
            top_rna_counts=top_rna_counts
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
            for block in frame_blocks[1:]:
                block = '=== 当前帧数:' + block
                try:
                    frame_data = self.parse_frame(block)
                    if frame_data.tick > 0:
                        self.frames.append(frame_data)
                except Exception as e:
                    continue
        
        # 按tick排序
        self.frames.sort(key=lambda f: f.tick)
        print(f"共解析 {len(self.frames)} 帧数据")
        
        # 为所有出现过的序列分配颜色
        self._assign_colors()
    
    def _assign_colors(self):
        """为DNA和RNA序列分配固定颜色"""
        all_dna_seqs = set()
        all_rna_seqs = set()
        
        for frame in self.frames:
            all_dna_seqs.update(frame.top_dna_counts.keys())
            all_rna_seqs.update(frame.top_rna_counts.keys())
        
        for i, seq in enumerate(sorted(all_dna_seqs)):
            self.dna_color_map[seq] = self.colors[i % len(self.colors)]
        
        for i, seq in enumerate(sorted(all_rna_seqs)):
            self.rna_color_map[seq] = self.colors[i % len(self.colors)]
    
    def create_dna_animation(self, interval: int = 100, save_path: str = None):
        """创建DNA演化动画"""
        if not self.frames:
            print("没有数据可生成动画")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('DNA 种群演化动画', fontsize=16, fontweight='bold')
        
        def animate(frame_idx):
            ax1.clear()
            ax2.clear()
            
            frame = self.frames[frame_idx]
            
            # 上图：堆叠面积图 - DNA种群组成
            if frame.top_dna_counts:
                sequences = list(frame.top_dna_counts.keys())
                counts = list(frame.top_dna_counts.values())
                colors = [self.dna_color_map.get(seq, 'gray') for seq in sequences]
                
                # 计算百分比
                percentages = [c / frame.total_cells * 100 for c in counts]
                
                # 横向堆叠条形图
                left = 0
                for seq, pct, color in zip(sequences, percentages, colors):
                    ax1.barh(0, pct, left=left, height=0.5, color=color, 
                            edgecolor='white', linewidth=0.5)
                    # 只在足够宽的区域显示标签
                    if pct > 5:
                        ax1.text(left + pct/2, 0, f'{pct:.1f}%', 
                               ha='center', va='center', fontsize=9, fontweight='bold')
                    left += pct
                
                ax1.set_xlim(0, 100)
                ax1.set_ylim(-0.5, 0.5)
                ax1.set_xlabel('种群占比 (%)', fontsize=12)
                ax1.set_yticks([])
                ax1.set_title(f'Tick {frame.tick} | 总细胞: {frame.total_cells} | DNA种类: {frame.dna_diversity}', 
                            fontsize=12, fontweight='bold')
                ax1.grid(axis='x', alpha=0.3)
                
                # 添加图例
                legend_elements = [plt.Rectangle((0,0),1,1, fc=self.dna_color_map.get(seq, 'gray'), 
                                                edgecolor='white', linewidth=0.5)
                                 for seq in sequences]
                ax1.legend(legend_elements, sequences, loc='upper left', 
                          bbox_to_anchor=(1.02, 1), fontsize=8, ncol=1)
            
            # 下图：柱状图 - 前10名DNA数量
            if frame.top_dna_counts:
                sequences = list(frame.top_dna_counts.keys())[:10]
                counts = [frame.top_dna_counts[seq] for seq in sequences]
                colors = [self.dna_color_map.get(seq, 'gray') for seq in sequences]
                
                bars = ax2.bar(range(len(sequences)), counts, color=colors, 
                              edgecolor='white', linewidth=1)
                ax2.set_xlabel('DNA 排名', fontsize=12)
                ax2.set_ylabel('细胞数量', fontsize=12)
                ax2.set_title('Top 10 DNA 种群数量', fontsize=12, fontweight='bold')
                ax2.set_xticks(range(len(sequences)))
                ax2.set_xticklabels([f'#{i+1}' for i in range(len(sequences))], fontsize=10)
                ax2.grid(axis='y', alpha=0.3)
                
                # 在柱子上方显示数值
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(count)}',
                           ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
        
        print("正在生成DNA动画...")
        
        # 创建进度条包装器
        pbar = tqdm(total=len(self.frames), desc="渲染帧", unit="帧")
        
        def animate_with_progress(frame_idx):
            animate(frame_idx)
            pbar.update(1)
        
        anim = animation.FuncAnimation(fig, animate_with_progress, frames=len(self.frames),
                                      interval=interval, repeat=False)
        
        if save_path is None:
            save_path = self.log_dir / f"dna_evolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # 保存为MP4
        print(f"\n保存视频到: {save_path}")
        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=10, bitrate=1800)
        
        # 使用 progress_callback 显示保存进度
        save_pbar = tqdm(total=len(self.frames), desc="编码视频", unit="帧")
        anim.save(save_path, writer=writer, progress_callback=lambda i, n: save_pbar.update(1))
        save_pbar.close()
        pbar.close()
        
        print(f"✅ DNA动画已保存到: {save_path}")
        
        plt.close()
        return anim
    
    def create_rna_animation(self, interval: int = 100, save_path: str = None):
        """创建RNA演化动画"""
        if not self.frames:
            print("没有数据可生成动画")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('RNA 种群演化动画', fontsize=16, fontweight='bold')
        
        def animate(frame_idx):
            ax1.clear()
            ax2.clear()
            
            frame = self.frames[frame_idx]
            
            # 上图：堆叠面积图 - RNA种群组成
            if frame.top_rna_counts:
                sequences = list(frame.top_rna_counts.keys())
                counts = list(frame.top_rna_counts.values())
                colors = [self.rna_color_map.get(seq, 'gray') for seq in sequences]
                
                # 计算百分比
                percentages = [c / frame.total_cells * 100 for c in counts]
                
                # 横向堆叠条形图
                left = 0
                for seq, pct, color in zip(sequences, percentages, colors):
                    ax1.barh(0, pct, left=left, height=0.5, color=color, 
                            edgecolor='white', linewidth=0.5)
                    if pct > 5:
                        ax1.text(left + pct/2, 0, f'{pct:.1f}%', 
                               ha='center', va='center', fontsize=9, fontweight='bold')
                    left += pct
                
                ax1.set_xlim(0, 100)
                ax1.set_ylim(-0.5, 0.5)
                ax1.set_xlabel('种群占比 (%)', fontsize=12)
                ax1.set_yticks([])
                ax1.set_title(f'Tick {frame.tick} | 总细胞: {frame.total_cells} | RNA种类: {frame.rna_diversity}', 
                            fontsize=12, fontweight='bold')
                ax1.grid(axis='x', alpha=0.3)
                
                # 添加图例
                legend_elements = [plt.Rectangle((0,0),1,1, fc=self.rna_color_map.get(seq, 'gray'), 
                                                edgecolor='white', linewidth=0.5)
                                 for seq in sequences]
                ax1.legend(legend_elements, sequences, loc='upper left', 
                          bbox_to_anchor=(1.02, 1), fontsize=8, ncol=1)
            
            # 下图：柱状图 - 前10名RNA数量
            if frame.top_rna_counts:
                sequences = list(frame.top_rna_counts.keys())[:10]
                counts = [frame.top_rna_counts[seq] for seq in sequences]
                colors = [self.rna_color_map.get(seq, 'gray') for seq in sequences]
                
                bars = ax2.bar(range(len(sequences)), counts, color=colors, 
                              edgecolor='white', linewidth=1)
                ax2.set_xlabel('RNA 排名', fontsize=12)
                ax2.set_ylabel('细胞数量', fontsize=12)
                ax2.set_title('Top 10 RNA 种群数量', fontsize=12, fontweight='bold')
                ax2.set_xticks(range(len(sequences)))
                ax2.set_xticklabels([f'#{i+1}' for i in range(len(sequences))], fontsize=10)
                ax2.grid(axis='y', alpha=0.3)
                
                # 在柱子上方显示数值
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(count)}',
                           ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
        
        print("正在生成RNA动画...")
        
        # 创建进度条包装器
        pbar = tqdm(total=len(self.frames), desc="渲染帧", unit="帧")
        
        def animate_with_progress(frame_idx):
            animate(frame_idx)
            pbar.update(1)
        
        anim = animation.FuncAnimation(fig, animate_with_progress, frames=len(self.frames),
                                      interval=interval, repeat=False)
        
        if save_path is None:
            save_path = self.log_dir / f"rna_evolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # 保存为MP4
        print(f"\n保存视频到: {save_path}")
        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=10, bitrate=1800)
        
        # 使用 progress_callback 显示保存进度
        save_pbar = tqdm(total=len(self.frames), desc="编码视频", unit="帧")
        anim.save(save_path, writer=writer, progress_callback=lambda i, n: save_pbar.update(1))
        save_pbar.close()
        pbar.close()
        
        print(f"✅ RNA动画已保存到: {save_path}")
        
        plt.close()
        return anim
    
    def create_combined_animation(self, interval: int = 100, save_path: str = None):
        """创建DNA和RNA组合动画"""
        if not self.frames:
            print("没有数据可生成动画")
            return
        
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        ax_dna_comp = fig.add_subplot(gs[0, 0])
        ax_rna_comp = fig.add_subplot(gs[0, 1])
        ax_dna_bar = fig.add_subplot(gs[1, 0])
        ax_rna_bar = fig.add_subplot(gs[1, 1])
        ax_stats = fig.add_subplot(gs[2, :])
        
        fig.suptitle('FaunaFuck 完整演化动画', fontsize=18, fontweight='bold')
        
        # 收集历史数据用于下方统计图
        history_ticks = []
        history_total = []
        history_dna_div = []
        history_rna_div = []
        
        def animate(frame_idx):
            for ax in [ax_dna_comp, ax_rna_comp, ax_dna_bar, ax_rna_bar, ax_stats]:
                ax.clear()
            
            frame = self.frames[frame_idx]
            
            # 更新历史数据
            history_ticks.append(frame.tick)
            history_total.append(frame.total_cells)
            history_dna_div.append(frame.dna_diversity)
            history_rna_div.append(frame.rna_diversity)
            
            # DNA组成
            if frame.top_dna_counts:
                sequences = list(frame.top_dna_counts.keys())[:8]
                percentages = [frame.top_dna_counts[seq] / frame.total_cells * 100 for seq in sequences]
                colors = [self.dna_color_map.get(seq, 'gray') for seq in sequences]
                
                left = 0
                for seq, pct, color in zip(sequences, percentages, colors):
                    ax_dna_comp.barh(0, pct, left=left, height=0.6, color=color, edgecolor='white')
                    if pct > 3:
                        ax_dna_comp.text(left + pct/2, 0, f'{pct:.1f}%', 
                                       ha='center', va='center', fontsize=8, fontweight='bold')
                    left += pct
                
                ax_dna_comp.set_xlim(0, 100)
                ax_dna_comp.set_ylim(-0.5, 0.5)
                ax_dna_comp.set_xlabel('DNA 种群占比 (%)', fontsize=10)
                ax_dna_comp.set_yticks([])
                ax_dna_comp.set_title(f'DNA 组成 (种类: {frame.dna_diversity})', fontsize=11, fontweight='bold')
                ax_dna_comp.grid(axis='x', alpha=0.3)
            
            # RNA组成
            if frame.top_rna_counts:
                sequences = list(frame.top_rna_counts.keys())[:8]
                percentages = [frame.top_rna_counts[seq] / frame.total_cells * 100 for seq in sequences]
                colors = [self.rna_color_map.get(seq, 'gray') for seq in sequences]
                
                left = 0
                for seq, pct, color in zip(sequences, percentages, colors):
                    ax_rna_comp.barh(0, pct, left=left, height=0.6, color=color, edgecolor='white')
                    if pct > 3:
                        ax_rna_comp.text(left + pct/2, 0, f'{pct:.1f}%', 
                                       ha='center', va='center', fontsize=8, fontweight='bold')
                    left += pct
                
                ax_rna_comp.set_xlim(0, 100)
                ax_rna_comp.set_ylim(-0.5, 0.5)
                ax_rna_comp.set_xlabel('RNA 种群占比 (%)', fontsize=10)
                ax_rna_comp.set_yticks([])
                ax_rna_comp.set_title(f'RNA 组成 (种类: {frame.rna_diversity})', fontsize=11, fontweight='bold')
                ax_rna_comp.grid(axis='x', alpha=0.3)
            
            # DNA柱状图
            if frame.top_dna_counts:
                sequences = list(frame.top_dna_counts.keys())[:6]
                counts = [frame.top_dna_counts[seq] for seq in sequences]
                colors = [self.dna_color_map.get(seq, 'gray') for seq in sequences]
                
                bars = ax_dna_bar.bar(range(len(sequences)), counts, color=colors, edgecolor='white')
                ax_dna_bar.set_ylabel('细胞数量', fontsize=10)
                ax_dna_bar.set_title('Top DNA 数量', fontsize=11, fontweight='bold')
                ax_dna_bar.set_xticks(range(len(sequences)))
                ax_dna_bar.set_xticklabels([f'#{i+1}' for i in range(len(sequences))], fontsize=9)
                ax_dna_bar.grid(axis='y', alpha=0.3)
            
            # RNA柱状图
            if frame.top_rna_counts:
                sequences = list(frame.top_rna_counts.keys())[:6]
                counts = [frame.top_rna_counts[seq] for seq in sequences]
                colors = [self.rna_color_map.get(seq, 'gray') for seq in sequences]
                
                bars = ax_rna_bar.bar(range(len(sequences)), counts, color=colors, edgecolor='white')
                ax_rna_bar.set_ylabel('细胞数量', fontsize=10)
                ax_rna_bar.set_title('Top RNA 数量', fontsize=11, fontweight='bold')
                ax_rna_bar.set_xticks(range(len(sequences)))
                ax_rna_bar.set_xticklabels([f'#{i+1}' for i in range(len(sequences))], fontsize=9)
                ax_rna_bar.grid(axis='y', alpha=0.3)
            
            # 统计趋势图
            ax_stats.plot(history_ticks, history_total, 'b-', linewidth=2, label='总细胞数')
            ax_stats_twin = ax_stats.twinx()
            ax_stats_twin.plot(history_ticks, history_dna_div, 'r-', linewidth=2, label='DNA多样性')
            ax_stats_twin.plot(history_ticks, history_rna_div, 'g-', linewidth=2, label='RNA多样性')
            
            ax_stats.set_xlabel('Tick (帧数)', fontsize=11)
            ax_stats.set_ylabel('总细胞数', fontsize=11, color='b')
            ax_stats_twin.set_ylabel('多样性 (种类数)', fontsize=11, color='r')
            ax_stats.set_title(f'演化趋势 - Tick {frame.tick}', fontsize=12, fontweight='bold')
            ax_stats.grid(True, alpha=0.3)
            ax_stats.tick_params(axis='y', labelcolor='b')
            ax_stats_twin.tick_params(axis='y', labelcolor='r')
            
            # 合并图例
            lines1, labels1 = ax_stats.get_legend_handles_labels()
            lines2, labels2 = ax_stats_twin.get_legend_handles_labels()
            ax_stats.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)
        
        print("正在生成组合动画...")
        
        # 创建进度条包装器
        pbar = tqdm(total=len(self.frames), desc="渲染帧", unit="帧")
        
        def animate_with_progress(frame_idx):
            animate(frame_idx)
            pbar.update(1)
        
        anim = animation.FuncAnimation(fig, animate_with_progress, frames=len(self.frames),
                                      interval=interval, repeat=False)
        
        if save_path is None:
            save_path = self.log_dir / f"combined_evolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # 保存为MP4
        print(f"\n保存视频到: {save_path}")
        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=10, bitrate=2400)
        
        # 使用 progress_callback 显示保存进度
        save_pbar = tqdm(total=len(self.frames), desc="编码视频", unit="帧")
        anim.save(save_path, writer=writer, progress_callback=lambda i, n: save_pbar.update(1))
        save_pbar.close()
        pbar.close()
        
        print(f"✅ 组合动画已保存到: {save_path}")
        
        plt.close()
        return anim


def main():
    """主函数"""
    import sys
    
    generator = AnimationGenerator("logs", top_n=10)
    
    print("开始加载日志文件...")
    generator.load_logs()
    
    if not generator.frames:
        print("未找到有效的日志数据")
        return
    
    print("\n选择要生成的动画类型:")
    print("1. DNA演化动画")
    print("2. RNA演化动画")
    print("3. DNA+RNA组合动画 (推荐)")
    print("4. 全部生成")
    
    choice = input("\n请输入选项 (1-4, 默认3): ").strip() or "3"
    
    if choice == "1":
        generator.create_dna_animation()
    elif choice == "2":
        generator.create_rna_animation()
    elif choice == "3":
        generator.create_combined_animation()
    elif choice == "4":
        generator.create_dna_animation()
        generator.create_rna_animation()
        generator.create_combined_animation()
    else:
        print("无效选项，生成组合动画")
        generator.create_combined_animation()
    
    print("\n✅ 动画生成完成！")


if __name__ == "__main__":
    main()
