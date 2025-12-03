#!/usr/bin/env python
"""
快速生成FaunaFuck演化动画（带进度条）
"""

from animation_generator import AnimationGenerator
import sys

def main():
    print("="*60)
    print("FaunaFuck 演化动画生成器")
    print("="*60)
    
    generator = AnimationGenerator("logs", top_n=10)
    
    print("\n📂 加载日志文件...")
    generator.load_logs()
    
    if not generator.frames:
        print("❌ 未找到有效的日志数据")
        return
    
    print(f"\n✅ 成功加载 {len(generator.frames)} 帧数据")
    print(f"   时间范围: Tick {generator.frames[0].tick} → {generator.frames[-1].tick}")
    print(f"   种群范围: {min(f.total_cells for f in generator.frames)} → {max(f.total_cells for f in generator.frames)} 个细胞")
    
    print("\n" + "="*60)
    print("开始生成DNA+RNA组合动画...")
    print("="*60 + "\n")
    
    try:
        generator.create_combined_animation()
        print("\n" + "="*60)
        print("✅ 动画生成完成！")
        print("="*60)
    except Exception as e:
        print(f"\n❌ 生成动画时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
