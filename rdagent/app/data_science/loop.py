# -*- coding: utf-8 -*-
"""
数据科学应用主循环模块

本模块提供RD-Agent数据科学场景的主要入口点和执行逻辑，支持：
1. 端到端的数据科学实验自动化
2. 灵活的参数配置和恢复机制
3. 多种执行模式和调试选项
4. 竞赛特定的优化和配置

使用场景：
- 通用机器学习竞赛（如Kaggle）
- 数据分析和建模任务
- 自动化特征工程和模型选择
- 端到端的数据科学流水线

作者: RD-Agent Team
"""

import asyncio
from pathlib import Path
from typing import Optional

import fire
import typer
from typing_extensions import Annotated

from rdagent.app.data_science.conf import DS_RD_SETTING
from rdagent.core.utils import import_class
from rdagent.log import rdagent_logger as logger
from rdagent.scenarios.data_science.loop import DataScienceRDLoop


def main(
    path: Optional[str] = None,
    checkout: Annotated[bool, typer.Option("--checkout/--no-checkout", "-c/-C")] = True,
    checkout_path: Optional[str] = None,
    step_n: Optional[int] = None,
    loop_n: Optional[int] = None,
    timeout: Optional[str] = None,
    competition="bms-molecular-translation",
    replace_timer=True,
    exp_gen_cls: Optional[str] = None,
):
    """
    数据科学实验主函数

    这是RD-Agent数据科学场景的主要入口点，负责启动端到端的机器学习实验自动化流程。

    Args:
        path: 实验恢复路径，用于从中断点继续执行
             如果指定，系统将加载指定路径的状态并继续实验
        checkout: 是否启用代码检出机制
                True: 自动从版本控制系统检出相关代码
                False: 使用当前工作目录的代码
        checkout_path: 代码检出的目标路径
                      如果为None，将使用默认路径
        step_n: 指定执行的步数限制
               None: 使用配置中的默认步数
               整数: 强制覆盖配置中的步数设置
        loop_n: 指定执行的循环次数限制
               None: 使用配置中的默认循环次数
               整数: 强制覆盖配置中的循环次数设置
        timeout: 实验超时时间，支持多种格式：
                "3600": 3600秒
                "1h": 1小时
                "30m": 30分钟
                None: 使用配置中的默认超时
        competition: 竞赛标识符，用于加载竞赛特定的配置和数据
                   默认为"bms-molecular-translation"
        replace_timer: 是否替换计时器机制
                      True: 使用新的计时器实现
                      False: 保持原有计时器
        exp_gen_cls: 自定义实验生成器类名
                    格式: "module.ClassName"
                    None: 使用默认的实验生成器

    Returns:
        None: 函数执行完成后直接退出，结果通过日志和输出文件记录

    Raises:
        ImportError: 当exp_gen_cls指定的类无法导入时
        ValueError: 当参数不合法或配置冲突时
        FileNotFoundError: 当指定的路径不存在时

    Example:
        >>> # 基础执行
        >>> python -m rdagent.app.data_science.loop --competition "playground-series-s4e9"

        >>> # 从断点恢复
        >>> python -m rdagent.app.data_science.loop --path ./workspace/experiment_001

        >>> # 自定义参数
        >>> python -m rdagent.app.data_science.loop \
        ...     --competition "titanic" \
        ...     --loop-n 5 \
        ...     --timeout "2h" \
        ...     --no-checkout

    Configuration:
        函数会自动加载以下配置源（优先级从高到低）：
        1. CLI参数
        2. 环境变量 (DS_RD_SETTING_*)
        3. 配置文件
        4. 默认值

    Logging:
        - 所有操作都会通过结构化日志记录
        - 支持多种日志级别 (DEBUG, INFO, WARNING, ERROR)
        - 日志同时输出到控制台和文件

    Execution Flow:
        1. 参数验证和配置加载
        2. 环境检查和依赖验证
        3. 实验空间初始化或恢复
        4. 启动DataScienceRDLoop主循环
        5. 结果保存和清理
    """
        A path like `$LOG_PATH/__session__/1/0_propose`. This indicates that we restore the state after finishing step 0 in loop 1.
    checkout :
        Used to control the log session path. Boolean type, default is True.
        - If True, the new loop will use the existing folder and clear logs for sessions after the one corresponding to the given path.
        - If False, the new loop will use the existing folder but keep the logs for sessions after the one corresponding to the given path.
    checkout_path:
        If a checkout_path (or a str like Path) is provided, the new loop will be saved to that path, leaving the original path unchanged.
    step_n :
        Number of steps to run; if None, the process will run indefinitely until an error or KeyboardInterrupt occurs.
    loop_n :
        Number of loops to run; if None, the process will run indefinitely until an error or KeyboardInterrupt occurs.
        - If the current loop is incomplete, it will be counted as the first loop for completion.
        - If both step_n and loop_n are provided, the process will stop as soon as either condition is met.
    competition :
        Competition name.
    replace_timer :
        If a session is loaded, determines whether to replace the timer with session.timer.
    exp_gen_cls :
        When there are different stages, the exp_gen can be replaced with the new proposal.


    Auto R&D Evolving loop for models in a Kaggle scenario.
    You can continue running a session by using the command:
    .. code-block:: bash
        dotenv run -- python rdagent/app/data_science/loop.py [--competition titanic] $LOG_PATH/__session__/1/0_propose  --step_n 1   # `step_n` is an optional parameter
        rdagent kaggle --competition playground-series-s4e8  # This command is recommended.
    """
    if not checkout_path is None:
        checkout = Path(checkout_path)

    if competition is not None:
        DS_RD_SETTING.competition = competition

    if not DS_RD_SETTING.competition:
        logger.error("Please specify competition name.")

    if path is None:
        kaggle_loop = DataScienceRDLoop(DS_RD_SETTING)
    else:
        kaggle_loop: DataScienceRDLoop = DataScienceRDLoop.load(path, checkout=checkout, replace_timer=replace_timer)

    # replace exp_gen if we have new class
    if exp_gen_cls is not None:
        kaggle_loop.exp_gen = import_class(exp_gen_cls)(kaggle_loop.exp_gen.scen)

    asyncio.run(kaggle_loop.run(step_n=step_n, loop_n=loop_n, all_duration=timeout))


if __name__ == "__main__":
    fire.Fire(main)
