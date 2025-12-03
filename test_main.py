# main.py
from collections import Counter

from world import World  # 你自己现有的
from gui import run_gui  # 刚才写的 gui.py


# 全局 world（简单粗暴但好用）
world = None
current_step = 0


def init_world():
    global world, current_step
    # TODO: 按你原先的初始化方式来构造 world
    world = World(...)
    current_step = 0


def collect_stats():
    """从当前 world 里统计 DNA / RNA 长度分布"""
    dna_len_counts = Counter()
    rna_len_counts = Counter()

    # 下面这段根据你自己的数据结构改：
    # 比如 world.cells 是 cell 列表，每个 cell 有 dna / rna 字符串
    for cell in world.cells:  # 这里 world.cells 只是举例
        if hasattr(cell, "dna") and cell.dna is not None:
            dna_len_counts[len(cell.dna)] += 1
        if hasattr(cell, "rna") and cell.rna is not None:
            rna_len_counts[len(cell.rna)] += 1

    return dna_len_counts, rna_len_counts


def step_simulation():
    """
    被 GUI 定时调用：
      1. 推进一次模拟
      2. 统计并返回当前 DNA / RNA 分布
    """
    global current_step

    # 1. 推进 world
    world.step()
    current_step += 1

    # 2. 收集统计
    dna_len_counts, rna_len_counts = collect_stats()

    # 3. 返回给 GUI
    return {
        "dna_len_counts": dna_len_counts,
        "rna_len_counts": rna_len_counts,
        "step": current_step,
    }


if __name__ == "__main__":
    init_world()
    run_gui(step_simulation)