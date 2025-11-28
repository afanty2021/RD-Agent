# -*- coding: utf-8 -*-
"""
CoSTEER 多进程进化策略模块

本模块实现了CoSTEER框架的核心进化策略，提供：
1. 多进程并行任务执行能力
2. 基于历史反馈的智能任务调度
3. 知识驱动的代码复用和改进
4. 改进模式下的选择性任务实现

CoSTEER (Collaborative Self-adaptive Testing and Evaluation for Evolutionary Refinement)
是RD-Agent的核心进化编码框架，通过持续的评估反馈循环实现代码的自主改进。

作者: RD-Agent Team
"""

from __future__ import annotations

from abc import abstractmethod

from rdagent.components.coder.CoSTEER.config import CoSTEERSettings
from rdagent.components.coder.CoSTEER.evaluators import (
    CoSTEERMultiFeedback,
    CoSTEERSingleFeedback,
)
from rdagent.components.coder.CoSTEER.evolvable_subjects import EvolvingItem
from rdagent.components.coder.CoSTEER.knowledge_management import (
    CoSTEERQueriedKnowledge,
)
from rdagent.core.conf import RD_AGENT_SETTINGS
from rdagent.core.evolving_framework import EvolvingStrategy, EvoStep, QueriedKnowledge
from rdagent.core.experiment import FBWorkspace, Task
from rdagent.core.scenario import Scenario
from rdagent.core.utils import multiprocessing_wrapper


class MultiProcessEvolvingStrategy(EvolvingStrategy):
    """
    多进程进化策略基类

    实现CoSTEER框架的核心进化逻辑，支持多进程并行执行任务。
    通过分析历史反馈和查询知识，智能地调度和改进代码实现。

    关键特性：
    - 多进程并行任务执行
    - 基于历史反馈的任务优先级调度
    - 知识库驱动的成功经验复用
    - 改进模式下的选择性任务实现
    """

    # 特殊键名：变更摘要
    KEY_CHANGE_SUMMARY = "__change_summary__"
    """用于记录进化主体变更摘要的特殊键名（可选）"""

    def __init__(self, scen: Scenario, settings: CoSTEERSettings, improve_mode: bool = False):
        """
        初始化多进程进化策略

        Args:
            scen: 场景实例，提供进化所需的上下文信息
            settings: CoSTEER配置设置
            improve_mode: 改进模式标志
                          - False: 正常模式，第一轮会实现所有任务
                          - True: 改进模式，仅实现之前失败的任务
        """
        super().__init__(scen)
        self.settings = settings
        self.improve_mode = improve_mode
        """
        改进模式说明：
        在改进模式下，系统只会实现之前失败过或需要改进的任务。
        这与正常模式的主要区别在于：第一轮不会实现所有任务，
        而是专注于需要改进的部分。
        """

    @abstractmethod
    def implement_one_task(
        self,
        target_task: Task,
        queried_knowledge: QueriedKnowledge | None = None,
        workspace: FBWorkspace | None = None,
        prev_task_feedback: CoSTEERSingleFeedback | None = None,
    ) -> dict[str, str]:
        """
        实现单个任务的抽象方法

        该方法接收任务描述和当前工作空间，输出需要应用到工作空间的修改。
        输出格式为：{文件名: 文件内容}，用于替换工作空间中的相应文件。

        Args:
            target_task: 需要实现的目标任务
            queried_knowledge: 从知识库查询到的相关知识（可选）
            workspace: 当前的工作空间状态（可选）
            prev_task_feedback: 上一轮进化步骤的任务反馈（可选）
                               None表示这是第一轮循环

        Returns:
            dict[str, str]: 需要更新到工作空间的新文件字典
                          - 键：文件名
                          - 值：文件内容
                          - 特殊键：self.KEY_CHANGE_SUMMARY 用于变更摘要

        Raises:
            NotImplementedError: 子类必须实现此方法

        Note:
            TODO: 需要修复之前实现的接口问题
        """
        raise NotImplementedError

    @abstractmethod
    def assign_code_list_to_evo(self, code_list: list[dict], evo: EvolvingItem) -> None:
        """
        将代码列表分配给进化主体

        由于implement_one_task方法接收workspace作为输入并输出修改，
        我们需要将这些实现应用到进化主体上。

        Args:
            code_list: 代码实现列表，与进化主体的子任务一一对应
                      如果某个任务未实现，则在列表中放置None
            evo: 需要更新的进化主体

        Raises:
            NotImplementedError: 子类必须实现此方法

        Note:
            代码列表的结构：
            - 长度与evo.sub_tasks相同
            - 每个元素对应一个子任务的实现
            - 未实现的子任务对应None
        """
        raise NotImplementedError

    def evolve(
        self,
        *,
        evo: EvolvingItem,
        queried_knowledge: CoSTEERQueriedKnowledge | None = None,
        evolving_trace: list[EvoStep] = [],
        **kwargs,
    ) -> EvolvableSubjects:
        """
        执行进化操作的核心方法

        这是CoSTEER框架的核心进化逻辑，通过以下步骤实现代码的进化：
        1. 识别需要实现的子任务
        2. 复用已成功任务的实现
        3. 并行执行待实现的任务
        4. 更新进化主体

        Args:
            evo: 需要进化的主体，包含多个子任务
            queried_knowledge: 查询到的相关知识，包含成功和失败的任务信息
            evolving_trace: 历史进化轨迹，用于获取上一轮的反馈信息
            **kwargs: 其他参数

        Returns:
            EvolvableSubjects: 进化后的主体实例

        Raises:
            AssertionError: 当历史反馈类型不匹配时抛出
        """
        # 初始化代码列表，长度与子任务数量相同
        code_list = [None for _ in range(len(evo.sub_tasks))]

        # 获取上一轮的反馈信息
        last_feedback = None
        if len(evolving_trace) > 0:
            last_feedback = evolving_trace[-1].feedback
            assert isinstance(last_feedback, CoSTEERMultiFeedback), "历史反馈必须是CoSTEERMultiFeedback类型"

        # ==================== 1. 任务识别阶段 ====================
        # 找出需要进化实现的任务索引
        to_be_finished_task_index: list[int] = []

        for index, target_task in enumerate(evo.sub_tasks):
            target_task_desc = target_task.get_task_information()

            # 情况1：任务已有成功实现，直接复用
            if target_task_desc in queried_knowledge.success_task_to_knowledge_dict:
                """
                注意：这里的逻辑依赖于知识库来确定已完成的任务
                这种设计允许知识库驱动的智能复用机制
                """
                code_list[index] = queried_knowledge.success_task_to_knowledge_dict[
                    target_task_desc
                ].implementation.file_dict
            else:
                # 情况2：需要决定是否实现该任务
                # 调度条件：
                # - 任务未被标记为失败
                # - 在改进模式下，确实有之前的失败反馈可供参考

                # 判断是否因改进模式而跳过任务
                skip_for_improve_mode = self.improve_mode and (
                    last_feedback is None  # 没有历史反馈
                    or (isinstance(last_feedback, CoSTEERMultiFeedback) and last_feedback[index] is None)  # 上轮此任务无反馈
                )

                # 决定是否将任务加入待实现列表
                if target_task_desc not in queried_knowledge.failed_task_info_set and not skip_for_improve_mode:
                    to_be_finished_task_index.append(index)

                # 为跳过的任务分配空实现（但仍会被assign_code_list_to_evo处理）
                if skip_for_improve_mode:
                    code_list[index] = {}  # 空实现表示跳过

        # ==================== 2. 并行执行阶段 ====================
        # 使用多进程并行实现待完成的任务
        result = multiprocessing_wrapper(
            [
                (
                    self.implement_one_task,
                    (
                        evo.sub_tasks[target_index],           # 目标任务
                        queried_knowledge,                     # 查询到的知识
                        evo.experiment_workspace,              # 实验工作空间
                        None if last_feedback is None else last_feedback[target_index],  # 历史反馈
                    ),
                )
                for target_index in to_be_finished_task_index
            ],
            n=RD_AGENT_SETTINGS.multi_proc_n,  # 使用配置的进程数
        )

        # 将并行执行的结果映射回代码列表
        for index, target_index in enumerate(to_be_finished_task_index):
            code_list[target_index] = result[index]

        # ==================== 3. 结果整合阶段 ====================
        # 将代码实现分配给进化主体
        evo = self.assign_code_list_to_evo(code_list, evo)

        return evo
