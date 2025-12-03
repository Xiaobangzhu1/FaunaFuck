import random

from typing import List, Tuple
from config import CellConfig, MapConfig
import numpy as np

DNA_BASES = ['d', '+', '[', '!', '?']

global mutated 
mutated = False


def mutate_DNA(gene_DNA: str) -> Tuple[str, bool]:
    '''
    基因突变流水线：
    DNA → 选取断点 → 切分片段 → 复制片段 → 打乱 → 反转 → 连接 → 突变DNA
    '''
    def _break_to_segments(s: str, p) -> list[str]:
        def _pick_break_points(n: int, p: float) -> list[int]:
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
        n = len(s)
        break_points = _pick_break_points(n, p)
        segments = _split_by_points(s, break_points)
        return segments
        
    def _duplicate_segment(segments: list[str]) -> list[str]:
        def _duplicate_random_segment(segments: list[str]) -> list[str]:
            if not segments:
                return segments
            duplicated = random.choice(segments)
            return segments + [duplicated]

        def _drop_segment(segments: list[str]) -> list[str]:
            """删除随机索引的片段"""
            index = random.randrange(len(segments))
            return [seg for i, seg in enumerate(segments) if i != index]
        
        segments = _duplicate_random_segment(segments)
        segments = _drop_segment(segments)
        return segments

    def _shuffle_segments(segments: list[str]) -> list[str]:
        """打乱片段顺序，可能反转某些片段"""
        if not segments:
            return segments
        segments = segments[:]  # 复制一份
        random.shuffle(segments)
        # 随机反转某些片段
        for i in range(len(segments)):
            if random.random() < 0.5:
                segments[i] = segments[i][::-1]
        return segments

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

    def _possible(rate: float) -> bool:
        """以给定概率返回 True 或 False"""
        return random.random() < rate

    global mutated
    mutated = False
    mutated_DNA = gene_DNA
    n = len(gene_DNA)

    base_muatation_rate = CellConfig.base_muatation_rate
    gene_mutation_rate = CellConfig.gene_mutation_rate
    # 根据基因长度调整突变概率（越长越容易突变）

    # 流水线：选断点 → 切分 → 复制 → 打乱 → 反转 → 连接
    
    def _add_base(gene_DNA: str, index: int) -> str:
        base = random.choice(DNA_BASES)
        return gene_DNA[:index] + base + gene_DNA[index:]
    
    def _drop_base(gene_DNA: str, index: int) -> str:
        return gene_DNA[:index] + gene_DNA[index+1:]
    
    def _substitute_base(gene_DNA: str, index: int) -> str:
        base = random.choice(DNA_BASES)
        return gene_DNA[:index] + base + gene_DNA[index+1:]

    if _possible(base_muatation_rate):
        # 单碱基突变
        index = random.randrange(n)
        method = random.choice([_add_base, _drop_base, _substitute_base])
        gene_DNA = method(gene_DNA, index)

    segments = _break_to_segments(gene_DNA, gene_mutation_rate)
    if len(segments) == 1:
        return gene_DNA, False  # 无法切分，返回原序列
    segments = _duplicate_segment(segments)
    segments = _shuffle_segments(segments)
    mutated_DNA = _join_segments_with_connectors(segments)
    mutated = True
    return mutated_DNA, mutated

def transcript_DNA_to_RNA(gene_DNA: str) -> List[str]:
    '''将DNA转录为RNA'''
    # 简单起见，RNA序列与DNA序列相同
    def _cut_DNAs(DNA : str) -> List[str]:
            '''将基因序列切割为片段'''
            s = DNA
            tokens = []
            base_set = ['d', '+', '[']
            stop_set = ['??']
            duo_set = ['!d', '?d', '!+','?+','![', '?[', '!!', '??']
            tri_set = ['!?d', '?!d', '!?+', '?!+', '!?[', '?![']
            fraction = []
            i = 0
            while i < len(DNA):
                if i + 2 <= len(s) and s[i:i+2] in stop_set:
                    break
                # 三字符
                if i + 3 <= len(s) and s[i:i+3] in tri_set:
                    tokens.append(s[i:i+3])
                    i += 3
                    continue
                # 两字符
                if i + 2 <= len(s) and s[i:i+2] in duo_set:
                    tokens.append(s[i:i+2])
                    i += 2
                    continue
                # 单字符
                if s[i] in base_set:
                    tokens.append(s[i])
                    i += 1
                    continue
                # 噪声跳过
                i += 1

            return tokens
                
    def _translate_cutted_DNA(cutted_DNA: List[str]) -> List[str]:
            '''将切割后的DNA转录为RNA'''
            translate_dict = {
                'd' : 'd', '!d' : 'a', '?d' : 'w', '!?d' : 's', '?!d' : 's',
                '+' : '+', '!+' : '-', '?+' : ',', '!?+' : '.', '?!+' : '.',
                '[' : '[', '![' : ']', '?[' : '>', '!?[' : '<', '?![' : '<',
                '!!' : 'p'
            }
            translated_RNA = [translate_dict[token] for token in cutted_DNA if token in translate_dict]
            return translated_RNA

    def _match_RNA(translated_RNA: List[str]) -> List[str]:
            '''为括号添加跳转位置，丢弃没有配对的括号'''
            stack = []
            matched_indices = set()  # 记录成功配对的索引
            
            # 第一遍：找出所有配对的括号
            for i, command in enumerate(translated_RNA):
                if command == '[':
                    stack.append(i)
                elif command == ']':
                    if len(stack) > 0:
                        j = stack.pop()
                        matched_indices.add(i)
                        matched_indices.add(j)
            
            # 第二遍：构建结果，只保留配对的括号和非括号命令
            result = []
            index_map = {}  # 旧索引到新索引的映射
            
            for i, command in enumerate(translated_RNA):
                if command in ['[', ']']:
                    if i in matched_indices:
                        index_map[i] = len(result)
                        result.append(command)
                else:
                    result.append(command)
            
            # 第三遍：为配对的括号添加跳转位置
            stack = []
            for i, command in enumerate(result):
                if command == '[':
                    stack.append(i)
                elif command == ']':
                    if len(stack) > 0:
                        j = stack.pop()
                        result[j] = f'[{i}'
                        result[i] = f']{j}'
            
            return result


    RNA = _cut_DNAs(gene_DNA)
    RNA = _translate_cutted_DNA(RNA)
    RNA = _match_RNA(RNA)
    return RNA
        