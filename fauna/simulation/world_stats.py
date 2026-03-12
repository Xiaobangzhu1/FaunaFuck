from __future__ import annotations


def collect_rnas(world):
    rna_counts = {}
    for cell in world.cells:
        if not cell.dead:
            raw_rna = cell.gene_RNA
            rna = [item[0] for item in raw_rna if item != '']
            rna_str = ''.join(rna)
            rna_counts[rna_str] = rna_counts.get(rna_str, 0) + 1

    sorted_rnas = sorted(rna_counts.items(), key=lambda item: item[1], reverse=True)
    lines = [
        f"=== 收集到 {len(sorted_rnas)} 种不同的RNA，共 {len([c for c in world.cells if not c.dead])} 个细胞 ==="
    ]
    for index, (rna, count) in enumerate(sorted_rnas, 1):
        display_rna = rna if len(rna) <= 40 else rna[:37] + "..."
        lines.append(f"#{index:2d} | x{count:4d} | len={len(rna):3d} | {display_rna}")
    return '\n'.join(lines)


def collect_dnas(world) -> str:
    dna_counts = {}
    for cell in world.cells:
        if not cell.dead:
            dna_counts[cell.gene_DNA] = dna_counts.get(cell.gene_DNA, 0) + 1

    sorted_dnas = sorted(dna_counts.items(), key=lambda item: item[1], reverse=True)
    lines = [
        f"=== 收集到 {len(sorted_dnas)} 种不同的DNA，共 {len([c for c in world.cells if not c.dead])} 个细胞 ==="
    ]
    for index, (dna, count) in enumerate(sorted_dnas, 1):
        dna_parts = [dna[j:j + 2] for j in range(0, len(dna), 2)]
        display_dna = ' '.join(dna_parts)
        lines.append(f"#{index:2d} | x{count:4d} | len={len(display_dna):3d} | {display_dna}")
    return '\n'.join(lines)


def build_tick_summary(world) -> str:
    output_dna = collect_dnas(world)
    output_rna = collect_rnas(world)
    return f"=== 当前帧数: {world.ticks} ===\n{output_dna}\n{output_rna}"