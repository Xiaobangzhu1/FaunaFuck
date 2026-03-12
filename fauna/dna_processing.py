import random

from typing import List, Tuple
from .config import CellConfig, MapConfig
import numpy as np

DNA_BASES = ['!', '?', '>', '<']
TRANSCRIPTION_MODE = 2

TRANSLATE_DICT_MODE2 = {
    '!!': '+', '!?': ',', '!>': 'd', '!<': 'a',
    '?!': '.', '??': '-', '?>': 'w', '?<': 's',
    '>!': '[', '>?': '}', '>>': '>', '><': 'e',
    '<!': ']', '<?': '{', '<<': '<', '<>': 'b',
}

global TEST
TEST = False

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

def transcript_DNA_to_RNA(gene_DNA: str, mode: int = TRANSCRIPTION_MODE, **kwargs) -> List[str]:
    """将 DNA 按 MODE2 规则转录为 RNA。"""
    # Backward compatibility: older callers may still pass MODE=2.
    if 'MODE' in kwargs:
        mode = kwargs['MODE']
    if mode != TRANSCRIPTION_MODE:
        raise ValueError('Only MODE == 2 is supported')

    def _cut_dnas(dna: str) -> List[str]:
        """按两碱基切分，且仅转录 <> 与 >< 之间内容。"""
        rna_list = []
        i = 0
        transcript_switch = False
        while i < len(dna) - 1:
            bases = dna[i] + dna[i + 1]
            if bases == '<>':
                transcript_switch = True
                i += 2
                continue
            if not transcript_switch:
                i += 2
                continue
            if bases == '><':
                break
            rna_list.append(bases)
            i += 2
        return rna_list

    def _translate_cutted_dna(cutted_dna: List[str]) -> List[str]:
        """将切割后的 DNA 片段映射为 RNA 指令。"""
        return [TRANSLATE_DICT_MODE2[token] for token in cutted_dna if token in TRANSLATE_DICT_MODE2]

    def _match_rna(translated_rna: List[str]) -> List[str]:
        """为配对括号补跳转索引，并丢弃未配对括号。"""
        stack = []
        matched_indices = set()
        for i, command in enumerate(translated_rna):
            if command == '[':
                stack.append(i)
            elif command == ']':
                if stack:
                    j = stack.pop()
                    matched_indices.add(i)
                    matched_indices.add(j)

        result = []
        for i, command in enumerate(translated_rna):
            if command in ['[', ']']:
                if i in matched_indices:
                    result.append(command)
            else:
                result.append(command)

        stack = []
        for i, command in enumerate(result):
            if command == '[':
                stack.append(i)
            elif command == ']':
                if stack:
                    j = stack.pop()
                    result[j] = f'[{i}'
                    result[i] = f']{j}'
        return result

    rna = _cut_dnas(gene_DNA)
    if TEST:
        print(f"Cutted DNA: {rna}")
    rna = _translate_cutted_dna(rna)
    if TEST:
        print(f"Translated RNA: {rna}")
    rna = _match_rna(rna)
    if TEST:
        print(f"Matched RNA: {rna}")
    return rna

if __name__ == "__main__":
    # 测试基因突变和转录
    TEST = True
    test_DNA = '!?<>?!??!+><!<<>?>!!'
    print(f"Original DNA: {test_DNA}")
    mutated_DNA, is_mutated = mutate_DNA(test_DNA)
    print(f"Mutated DNA: {mutated_DNA} (Mutated: {is_mutated})")
    RNA = transcript_DNA_to_RNA(mutated_DNA)
    print(f"Transcribed RNA: {RNA}")
