#!/usr/bin/env python3
"""
详细解析 RD-Agent 实验性能指标
"""
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def main():
    base_path = Path("/Users/berton/Github/RD-Agent/log/2025-12-27_09-27-43-735031")

    print("="*80)
    print(" RD-Agent 实验结果详细分析")
    print("="*80)

    # 1. 加载运行结果
    result_files = list((base_path / "Loop_0/running/runner result/26906").glob("*.pkl"))
    if not result_files:
        print("未找到运行结果文件")
        return

    with open(result_files[-1], 'rb') as f:
        experiment = pickle.load(f)

    # 2. 提取性能指标
    print("\n【实验性能指标】\n")

    if hasattr(experiment, 'running_info'):
        running_info = experiment.running_info
        print(f"结果类型: {type(running_info)}")

        if hasattr(running_info, 'result'):
            result = running_info.result
            print(f"\n详细性能指标:\n")
            print(result)

    # 3. 提取反馈信息
    print("\n" + "="*80)
    print("【编码反馈与进化】\n")

    if hasattr(experiment, 'prop_dev_feedback'):
        feedback = experiment.prop_dev_feedback
        print(f"反馈类型: {type(feedback)}")

        if hasattr(feedback, 'feedback_list'):
            feedback_list = feedback.feedback_list
            print(f"共收到 {len(feedback_list)} 条反馈:\n")

            for i, fb in enumerate(feedback_list, 1):
                print(f"\n--- 反馈 {i} ---")
                if hasattr(fb, '__dict__'):
                    for k, v in fb.__dict__.items():
                        if not k.startswith('_'):
                            v_str = str(v)
                            if len(v_str) > 200:
                                v_str = v_str[:200] + "..."
                            print(f"  {k}: {v_str}")

    # 4. 查看因子执行结果
    print("\n" + "="*80)
    print("【因子执行结果】\n")

    if hasattr(experiment, 'sub_results'):
        sub_results = experiment.sub_results
        if sub_results:
            print("子任务结果:")
            for k, v in sub_results.items():
                print(f"  {k}: {v}")
        else:
            print("子任务结果为空（可能未单独保存）")

    # 5. 查看工作空间文件
    print("\n" + "="*80)
    print("【生成的代码文件】\n")

    if hasattr(experiment, 'sub_workspace_list'):
        workspaces = experiment.sub_workspace_list
        print(f"共生成 {len(workspaces)} 个工作空间:\n")
        for ws in workspaces:
            print(f"  - {ws}")

    # 6. 总结分析
    print("\n" + "="*80)
    print("【实验分析总结】\n")

    print("""
    实验特点:
    1. 因子类型: 动量因子、流动性因子、波动率因子、价格因子
    2. 时间周期: 10日、20日滚动窗口
    3. 计算方法: 简单数学统计（均值、标准差、比率）

    需要关注:
    1. IC值（Information Correlation）- 因子与收益的相关性
    2. Rank IC - 排名相关性
    3. 回撤（Max Drawdown）- 最大损失幅度
    4. 夏普比率（Sharpe Ratio）- 风险调整后收益
    """)

if __name__ == "__main__":
    main()
