#!/usr/bin/env python3
"""
解析 RD-Agent 实验结果的脚本
"""
import pickle
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def safe_load_pkl(file_path):
    """安全加载 pickle 文件"""
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        return None

def get_obj_info(obj):
    """获取对象信息"""
    if obj is None:
        return "None"
    elif isinstance(obj, (list, tuple)):
        return [get_obj_info(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: get_obj_info(v) for k, v in list(obj.items())[:5]}
    else:
        # 尝试获取对象的属性
        try:
            if hasattr(obj, '__dict__'):
                return {k: str(v)[:50] for k, v in list(obj.__dict__.items())[:5]}
            return str(obj)[:100]
        except:
            return str(type(obj))

def print_section(title, content=""):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if content:
        print(content)

def main():
    base_path = Path("/Users/berton/Github/RD-Agent/log/2025-12-27_09-27-43-735031")

    # 1. 查看实验生成的提案
    print_section("1. 实验提案 (Hypothesis)")

    exp_gen_files = list((base_path / "Loop_0/direct_exp_gen/experiment generation/26906").glob("*.pkl"))
    if exp_gen_files:
        data = safe_load_pkl(exp_gen_files[-1])
        if data is not None:
            # 直接打印数据类型和内容
            print(f"数据类型: {type(data)}")
            print(f"内容预览: {get_obj_info(data)}")

            # 如果是列表，尝试提取因子信息
            if isinstance(data, list) and len(data) > 0:
                print(f"\n共生成了 {len(data)} 个因子任务:\n")
                for i, item in enumerate(data[:10], 1):
                    # 尝试获取因子名称
                    if hasattr(item, '__class__'):
                        class_name = item.__class__.__name__
                        print(f"  {i}. {class_name}")
                        if hasattr(item, '__dict__'):
                            for k, v in item.__dict__.items():
                                if isinstance(v, str) and len(v) < 200:
                                    print(f"     {k}: {v}")
                            print()

    # 2. 查看运行结果
    print_section("2. 实验运行结果")

    result_files = list((base_path / "Loop_0/running/runner result/26906").glob("*.pkl"))
    if result_files:
        data = safe_load_pkl(result_files[-1])
        if data is not None:
            print(f"数据类型: {type(data)}")
            print(f"\n数据结构:\n{get_obj_info(data)}")

            # 尝试提取性能指标
            if hasattr(data, '__dict__'):
                print(f"\n对象属性:")
                for k, v in data.__dict__.items():
                    if not k.startswith('_'):
                        print(f"  {k}: {str(v)[:100]}")

    # 3. 查看回测图表文件
    print_section("3. 回测图表")

    chart_files = list((base_path / "Loop_0/running/Quantitative Backtesting Chart/26906").glob("*.pkl"))
    if chart_files:
        print(f"找到 {len(chart_files)} 个图表文件:")
        for f in chart_files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")

    # 4. 查看编码进化过程
    print_section("4. 编码进化过程")

    evo_loops = ['evo_loop_0', 'evo_loop_1', 'evo_loop_2']
    for loop_name in evo_loops:
        loop_path = base_path / f"Loop_0/coding/{loop_name}"
        if loop_path.exists():
            feedback_path = loop_path / "evolving feedback"
            if feedback_path.exists():
                feedback_files = list(feedback_path.glob("*.pkl"))
                if feedback_files:
                    print(f"\n{loop_name}:")
                    data = safe_load_pkl(feedback_files[-1])
                    if data is not None:
                        print(f"  类型: {type(data)}")
                        if hasattr(data, '__dict__'):
                            print(f"  属性: {list(data.__dict__.keys())[:10]}")

    # 5. 总结
    print_section("5. 实验总结")

    print(f"""
实验时间: 2025-12-27 09:27:43
总耗时: 约 26 分钟
完成的步骤:
  - direct_exp_gen (提案生成)
  - coding (编码实现，3轮进化)
  - running (回测执行)
  - feedback (反馈评估)

    """)

if __name__ == "__main__":
    main()
