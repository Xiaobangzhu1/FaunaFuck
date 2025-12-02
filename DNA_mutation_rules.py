import random

from typing import Tuple
from config import CellConfig, MapConfig
import numpy as np

DNA_BASES = ['d', '+', '[', '!', '?']

global mutated 
mutated = False

def _pick_break_points(n: int, p: float) -> list[int]:
    """按独立概率 p 从 0..n-1 中选择断点，返回升序索引列表。"""
    if n <= 0 or p <= 0.0:
        return []
    mask = np.random.rand(n) < p
    mutated = np.any(mask)
    return np.nonzero(mask)[0].astype(int).tolist()

def _split_by_points(s: str, points: list[int]) -> list[str]:
    """删除 points 上的字符，并按这些位置将字符串切为若干段。"""
    if not s:
        return []
    if not points:
        return [s]
    points = sorted(set([i for i in points if 0 <= i < len(s)]))
    segs = []
    prev = 0
    for idx in points:
        seg = s[prev:idx]
        if seg:
            segs.append(seg)
        prev = idx + 1  # 跳过被删除的碱基
    tail = s[prev:]
    if tail:
        segs.append(tail)
    return segs
    
def _duplicate_random_segment(segments: list[str]) -> list[str]:
    """复制一个随机片段，返回n+1个片段"""
    if not segments:
        return segments
    duplicated = random.choice(segments)
    return segments + [duplicated]

def _drop_segment(segments: list[str]) -> list[str]:
    """删除随机索引的片段"""
    index = random.randrange(len(segments))
    return [seg for i, seg in enumerate(segments) if i != index]

def _join_segments_with_connectors(segments: list[str]) -> str:
    """用随机碱基连接片段"""
    if not segments:
        return ''
    if len(segments) == 1:
        return segments[0]

    connectors = [random.choice(DNA_BASES) for _ in range(len(segments) - 1)]
    pieces = []
    for i, seg in enumerate(segments):
        pieces.append(seg)
        if i < len(connectors):
            pieces.append(connectors[i])
    return ''.join(pieces)

def mutate_DNA(gene_DNA: str) -> Tuple[str, bool]:
    '''
    基因突变流水线：
    DNA → 选取断点 → 切分片段 → 复制片段 → 打乱 → 反转 → 连接 → 突变DNA
    '''
    n = len(gene_DNA)

    base_rate = CellConfig.mutation_rate 
    
    if random.random() > base_rate:
        return gene_DNA, False
    # 流水线：选断点 → 切分 → 复制 → 打乱 → 反转 → 连接
    break_points = _pick_break_points(n, float(base_rate))
    segments = _split_by_points(gene_DNA, break_points)
    segments = _duplicate_random_segment(segments)
    segments = _drop_segment(segments)
    mutated_DNA = _join_segments_with_connectors(segments)
    
    return mutated_DNA, mutated