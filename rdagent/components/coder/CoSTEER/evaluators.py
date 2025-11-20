# -*- coding: utf-8 -*-
"""
CoSTEER 评估器模块

本模块实现了CoSTEER框架的核心评估系统，提供：
1. 四阶段评估反馈机制
2. 多任务并行评估支持
3. 评估结果聚合和整合
4. 向后兼容的反馈数据结构

评估流程：
- Execution: 代码执行结果评估
- Return Checking: 返回值验证（值、形状、生成标志等约束）
- Code: 代码质量检查
- Final Decision: 最终决策判断

作者: RD-Agent Team
"""

from abc import abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from rdagent.components.coder.CoSTEER.evolvable_subjects import EvolvingItem
from rdagent.core.conf import RD_AGENT_SETTINGS
from rdagent.core.evaluation import Evaluator, Feedback
from rdagent.core.evolving_framework import QueriedKnowledge
from rdagent.core.experiment import Task, Workspace
from rdagent.core.utils import multiprocessing_wrapper
from rdagent.log import rdagent_logger as logger

if TYPE_CHECKING:
    from rdagent.core.scenario import Scenario

# TODO:
# 1. It seems logically sound, but we currently lack a scenario to apply it.
# 2. If it proves to be useful, relocate it to a more general location.
#
# class FBWorkspaceExeFeedback(Feedback):
#     """
#     It pairs with FBWorkspace in the abstract level.
#     """
#     # ws: FBWorkspace   # potential
#     stdout: str


@dataclass
class CoSTEERSingleFeedback(Feedback):
    """
    CoSTEER单一任务反馈数据结构

    这是CoSTEER框架的核心反馈类，采用四阶段评估设计：
    1. Execution（代码执行）: 代码执行结果和错误信息
    2. Return Checking（返回值检查）: 返回值验证，包括值、形状、生成标志等约束检查
    3. Code（代码质量）: 生成的代码内容和质量评估
    4. Final Decision（最终决策）: 综合评估的最终成功/失败判断

    设计理念：
    - 与实现的代码阶段保持一致
    - 提供结构化的反馈信息
    - 支持多轮迭代的改进指导

    Attributes:
        execution: 代码执行结果反馈，包含执行输出或错误信息
        return_checking: 返回值检查反馈，包括值的正确性、形状匹配、生成标志等约束验证
                         如果没有返回值检查则为None
        code: 生成的代码内容，用于代码审查和质量分析
        final_decision: 最终决策布尔值，True表示成功，False表示失败，None表示未确定
    """
    execution: str
    """代码执行结果反馈，包含执行输出或错误信息"""

    return_checking: str | None
    """返回值检查反馈，包括测试中的所有约束检查（值、形状、生成标志等）"""

    code: str
    """生成的代码内容，用于代码审查和质量分析"""

    final_decision: bool | None = None
    """最终决策，True表示成功，False表示失败，None表示未确定"""

    @staticmethod
    def val_and_update_init_dict(data: dict) -> dict:
        """
        验证并更新初始化数据字典

        该方法主要用于在对象初始化前验证和转换数据字典，特别是处理final_decision字段。
        支持字符串类型的布尔值转换（"true"/"false" -> True/False）。

        TODO: 未来应使用更通用的验证方法，如Pydantic，来处理数据字典的验证和更新

        Args:
            data: 包含final_decision字段的数据字典
                  必须包含的键：'execution', 'return_checking', 'code', 'final_decision'

        Returns:
            dict: 更新后的数据字典，其中final_decision已转换为布尔类型

        Raises:
            ValueError: 当final_decision字段不存在或无法转换为布尔类型时抛出
            ValueError: 当execution、return_checking、code字段不是字符串类型时抛出

        Note:
            - 支持"true"/"True" -> True转换
            - 支持"false"/"False" -> False转换
            - 确保所有字符串字段都是有效的字符串类型
        """
        if "final_decision" not in data:
            raise ValueError("'final_decision' is required")

        if isinstance(data["final_decision"], str):
            if data["final_decision"] == "false" or data["final_decision"] == "False":
                data["final_decision"] = False
            elif data["final_decision"] == "true" or data["final_decision"] == "True":
                data["final_decision"] = True

        if not isinstance(data["final_decision"], bool):
            raise ValueError(f"'final_decision' must be a boolean, not {type(data['final_decision'])}")

        for attr in "execution", "return_checking", "code":
            if data[attr] is not None and not isinstance(data[attr], str):
                raise ValueError(f"'{attr}' must be a string, not {type(data[attr])}")
        return data

    @classmethod
    def merge(cls, feedback_li: list["CoSTEERSingleFeedback"]) -> "CoSTEERSingleFeedback":
        """
        合并多个反馈为单一反馈

        该方法将多个CoSTEERSingleFeedback对象合并为一个综合反馈。
        主要用于多评估器场景下，将不同评估器的反馈结果进行整合。

        合并策略：
        - final_decision: 采用所有反馈的AND逻辑（全部成功才算成功）
        - execution: 将所有非None的执行反馈用换行符连接
        - return_checking: 将所有非None的返回值检查反馈用换行符连接
        - code: 将所有非None的代码内容用换行符连接

        注意事项：
        - 当前实现仅基于CoSTEERSingleFeedback的基本属性进行合并
        - 如果使用CoSTEERSingleFeedback的复杂子类，可能会丢失信息
        - 建议在复杂场景下重写此方法以避免信息丢失

        Args:
            feedback_li: 需要合并的CoSTEERSingle反馈列表，至少包含一个元素

        Returns:
            CoSTEERSingleFeedback: 合并后的单一反馈对象

        Raises:
            IndexError: 当feedback_li为空列表时抛出

        Example:
            >>> fb1 = CoSTEERSingleFeedback("执行1", "检查1", "代码1", True)
            >>> fb2 = CoSTEERSingleFeedback("执行2", "检查2", "代码2", True)
            >>> merged = CoSTEERSingleFeedback.merge([fb1, fb2])
            >>> merged.final_decision  # True
            >>> merged.execution  # "执行1\n\n执行2"
        """

    def __str__(self) -> str:
        return f"""------------------Execution------------------
{self.execution}
------------------Return Checking------------------
{self.return_checking if self.return_checking is not None else 'No return checking'}
------------------Code------------------
{self.code}
------------------Final Decision------------------
This implementation is {'SUCCESS' if self.final_decision else 'FAIL'}.
"""

    def __bool__(self):
        return self.final_decision


class CoSTEERSingleFeedbackDeprecated(CoSTEERSingleFeedback):
    """This class is a base class for all code generator feedback to single implementation"""

    def __init__(
        self,
        execution_feedback: str = None,
        shape_feedback: str = None,
        code_feedback: str = None,
        value_feedback: str = None,
        final_decision: bool = None,
        final_feedback: str = None,
        value_generated_flag: bool = None,
        final_decision_based_on_gt: bool = None,
    ) -> None:
        self.execution_feedback = execution_feedback
        self.code_feedback = code_feedback
        self.value_feedback = value_feedback
        self.final_decision = final_decision
        self.final_feedback = final_feedback
        self.value_generated_flag = value_generated_flag
        self.final_decision_based_on_gt = final_decision_based_on_gt

        # TODO:
        # Not general enough. So we should not put them in the general costeer feedback
        # Instead, we should create subclass for it.
        self.shape_feedback = shape_feedback  # Not general enough. So

    @property
    def execution(self):
        return self.execution_feedback

    @execution.setter
    def execution(self, value):
        self.execution_feedback = value

    @property
    def return_checking(self):
        if self.value_generated_flag:
            return f"value feedback: {self.value_feedback}\n\nshape feedback: {self.shape_feedback}"
        return None

    @return_checking.setter
    def return_checking(self, value):
        # Since return_checking is derived from value_feedback and shape_feedback,
        # we don't need to do anything here
        self.value_feedback = value
        self.shape_feedback = value

    @property
    def code(self):
        return self.code_feedback

    @code.setter
    def code(self, value):
        self.code_feedback = value

    def __str__(self) -> str:
        return f"""------------------Execution Feedback------------------
{self.execution_feedback if self.execution_feedback is not None else 'No execution feedback'}
------------------Shape Feedback------------------
{self.shape_feedback if self.shape_feedback is not None else 'No shape feedback'}
------------------Code Feedback------------------
{self.code_feedback if self.code_feedback is not None else 'No code feedback'}
------------------Value Feedback------------------
{self.value_feedback if self.value_feedback is not None else 'No value feedback'}
------------------Final Feedback------------------
{self.final_feedback if self.final_feedback is not None else 'No final feedback'}
------------------Final Decision------------------
This implementation is {'SUCCESS' if self.final_decision else 'FAIL'}.
"""


class CoSTEERMultiFeedback(Feedback):
    """
    CoSTEER多任务反馈容器

    该类用于管理多个子任务的反馈结果，每个元素对应一个子任务的实现反馈。
    主要用于多任务并行评估场景，如多个因子实现、多个模型训练等。

    核心特性：
    - 容器式设计：支持索引、迭代、长度等标准容器操作
    - 灵活的任务管理：支持动态添加新的反馈
    - 智能完成判断：区分"可接受"和"已完成"两种状态
    - None值容忍：能够处理跳过的任务（None反馈）

    使用场景：
    - 量化因子开发：同时评估多个因子的实现质量
    - 模型集成开发：评估多个子模型的训练结果
    - 数据科学流程：评估数据处理流水线的各个步骤

    Attributes:
        feedback_list: CoSTEERSingle反馈列表，每个元素对应一个子任务的反馈
    """

    def __init__(self, feedback_list: List[CoSTEERSingleFeedback]) -> None:
        """
        初始化多任务反馈容器

        Args:
            feedback_list: CoSTEERSingle反馈列表，每个元素对应一个子任务的实现反馈
                         列表长度通常与子任务数量一致
        """
        self.feedback_list = feedback_list
        """CoSTEERSingle反馈列表，存储所有子任务的反馈结果"""

    def __getitem__(self, index: int) -> CoSTEERSingleFeedback:
        """
        通过索引获取指定子任务的反馈

        Args:
            index: 子任务索引位置

        Returns:
            CoSTEERSingleFeedback: 指定索引位置的子任务反馈

        Example:
            >>> multi_fb[0]  # 获取第一个子任务的反馈
        """
        return self.feedback_list[index]

    def __len__(self) -> int:
        """
        获取子任务总数

        Returns:
            int: 子任务的数量，即反馈列表的长度
        """
        return len(self.feedback_list)

    def append(self, feedback: CoSTEERSingleFeedback) -> None:
        """
        添加新的子任务反馈

        动态扩展反馈列表，用于处理新增的子任务或延迟添加反馈的场景。

        Args:
            feedback: 需要添加的CoSTEERSingle反馈对象
        """
        self.feedback_list.append(feedback)

    def __iter__(self):
        """
        返回反馈列表的迭代器

        支持for循环遍历所有子任务反馈。

        Returns:
            Iterator[CoSTEERSingleFeedback]: 反馈列表的迭代器

        Example:
            >>> for fb in multi_fb:
            ...     print(fb.final_decision)
        """
        return iter(self.feedback_list)

    def is_acceptable(self) -> bool:
        """
        检查所有反馈是否都可接受

        该方法调用每个反馈对象的is_acceptable方法，要求所有反馈都返回True。
        用于检查整体任务的可接受性，比__bool__方法更宽松。

        Returns:
            bool: 如果所有反馈都可接受则返回True，否则返回False

        Note:
            这是一个备用方法，当前实现与__bool__方法相同，
            但设计上允许子类提供不同的可接受性判断逻辑。
        """
        return all(feedback.is_acceptable() for feedback in self.feedback_list)

    def finished(self) -> bool:
        """
        检查任务是否已完成（忽略None反馈）

        在某些实现中，任务可能多次失败，导致智能体跳过实现，
        这会产生None反馈。但我们希望接受正确的部分并忽略None反馈。

        与__bool__的区别：
        - __bool__: 要求所有反馈都成功，包括None
        - finished(): 只要求非None的反馈都成功

        Returns:
            bool: 如果所有非None的反馈都成功则返回True，否则返回False

        Example:
            >>> # 有3个任务，第2个任务被跳过（None）
            >>> feedbacks = [fb1, None, fb3]
            >>> # 假设fb1和fb3都成功（final_decision=True）
            >>> finished = CoSTEERMultiFeedback(feedbacks).finished()  # True
            >>> bool_result = CoSTEERMultiFeedback(feedbacks).__bool__()  # False
        """
        return all(feedback.final_decision for feedback in self.feedback_list if feedback is not None)

    def __bool__(self) -> bool:
        """
        布尔值转换，检查所有反馈是否都成功

        该方法要求所有反馈（包括None）的final_decision都为True。
        这是最严格的成功判断标准。

        Returns:
            bool: 如果所有反馈的final_decision都为True则返回True，否则返回False

        Note:
            - 与finished()方法的区别在于对None反馈的处理
            - finished()忽略None反馈，而此方法将None视为失败
        """
        return all(feedback.final_decision for feedback in self.feedback_list)


class CoSTEEREvaluator(Evaluator):
    """
    CoSTEER单一任务评估器基类

    这是CoSTEER框架中所有评估器的抽象基类，定义了单一任务评估的标准接口。
    子类需要实现evaluate方法来提供具体的评估逻辑。

    设计理念：
    - 统一接口：为所有CoSTEER评估器提供一致的评估接口
    - 场景感知：评估器需要关联特定的场景上下文
    - 灵活扩展：支持通过继承实现各种评估策略

    使用场景：
    - 数据加载器评估：验证数据处理代码的正确性
    - 特征工程评估：检查特征生成代码的质量
    - 模型训练评估：评估模型实现和训练过程
    - 流水线评估：验证完整的数据科学流水线

    Attributes:
        scen: 关联的场景实例，提供评估所需的上下文信息和配置
    """

    def __init__(
        self,
        scen: "Scenario",
    ) -> None:
        """
        初始化CoSTEER评估器

        Args:
            scen: 场景实例，提供评估所需的上下文信息，包括数据配置、环境设置等
        """
        self.scen = scen
        """关联的场景实例，包含评估所需的上下文信息"""

    # TODO:
    # 未来应该为所有评估器提供统一接口，例如统一的参数命名和返回格式
    # 需要调整其他评估器的接口以保持一致性
    @abstractmethod
    def evaluate(
        self,
        target_task: Task,
        implementation: Workspace,
        gt_implementation: Workspace,
        **kwargs,
    ) -> CoSTEERSingleFeedback:
        """
        评估单一任务的实现

        这是评估器的核心抽象方法，子类必须实现此方法来提供具体的评估逻辑。
        评估过程应该按照CoSTEER的四阶段设计进行：
        1. 执行代码并收集结果
        2. 检查返回值是否符合预期
        3. 分析代码质量
        4. 做出最终成功/失败决策

        Args:
            target_task: 需要评估的目标任务，包含任务描述和要求
            implementation: 待评估的代码实现工作空间
            gt_implementation: 真实/标准的实现工作空间，用于对比验证
                           如果没有标准实现则为None
            **kwargs: 其他评估参数，如评估配置、超参数等

        Returns:
            CoSTEERSingleFeedback: 包含四阶段评估结果的反馈对象

        Raises:
            NotImplementedError: 子类必须实现此方法

        Note:
            - 评估应该是确定性的，相同的输入应该产生相同的评估结果
            - 评估过程应该记录详细的信息，便于后续分析和改进
            - final_decision应该基于所有阶段的综合判断
        """
        raise NotImplementedError("请实现 `evaluate` 方法")


class CoSTEERMultiEvaluator(CoSTEEREvaluator):
    """
    CoSTEER多任务评估器

    专门用于实验评估的多任务评估器，能够并行评估多个子任务。
    由于CoSTEER框架中一个实验通常包含多个子任务（如多个因子、多个模型等），
    该评估器提供高效的批量评估能力。

    核心特性：
    - 并行评估：支持多进程并行评估多个子任务，提高评估效率
    - 多评估器支持：可以同时使用多个不同的单一评估器
    - 反馈聚合：将多个评估器的结果智能聚合为统一的多任务反馈
    - 容错处理：能够处理部分任务评估失败的情况

    使用场景：
    - 量化因子开发：同时评估多个因子的实现质量
    - 集成模型开发：评估多个子模型的训练结果
    - 特征工程：批量评估多个特征生成器的效果
    - 数据科学流水线：评估流水线中各个组件的表现

    Attributes:
        single_evaluator: 单一评估器实例或评估器列表
                         - 如果是单一评估器，则用于评估所有子任务
                         - 如果是评估器列表，则每个评估器都会评估所有子任务，结果会被聚合
    """

    def __init__(self, single_evaluator: CoSTEEREvaluator | list[CoSTEEREvaluator], *args, **kwargs) -> None:
        """
        初始化多任务评估器

        Args:
            single_evaluator: 单一评估器实例或评估器列表
                            - CoSTEEREvaluator: 单个评估器，用于评估所有子任务
                            - list[CoSTEEREvaluator]: 多个评估器，每个都评估所有子任务
            *args: 传递给父类的其他位置参数
            **kwargs: 传递给父类的其他关键字参数

        Example:
            >>> # 使用单一评估器
            >>> evaluator = CoSTEERMultiEvaluator(single_evaluator=ModelEvaluator(scen))

            >>> # 使用多个评估器
            >>> evaluators = [ModelEvaluator(scen), CodeQualityEvaluator(scen)]
            >>> multi_evaluator = CoSTEERMultiEvaluator(single_evaluator=evaluators, scen=scen)
        """
        super().__init__(*args, **kwargs)
        self.single_evaluator = single_evaluator
        """单一评估器或评估器列表，用于执行具体的子任务评估"""

    def evaluate(
        self,
        evo: EvolvingItem,
        queried_knowledge: QueriedKnowledge = None,
        **kwargs,
    ) -> CoSTEERMultiFeedback:
        """
        并行评估多个子任务

        执行多任务评估的核心方法，包含两个主要阶段：
        1. 并行评估阶段：使用多进程并行评估每个子任务
        2. 反馈聚合阶段：将多个评估器的结果合并为统一的多任务反馈

        评估流程：
        - 准备评估器列表（支持单一或多个评估器）
        - 为每个评估器并行评估所有子任务
        - 沿子任务维度合并多个评估器的反馈
        - 记录最终决策统计信息
        - 更新进化主体的任务状态

        Args:
            evo: 进化主体，包含多个子任务和对应的工作空间
                  - evo.sub_tasks: 子任务列表
                  - evo.sub_workspace_list: 子任务工作空间列表
                  - evo.sub_gt_implementations: 标准实现列表（可选）
            queried_knowledge: 查询到的知识库信息（可选）
                              可用于指导评估过程或提供额外的上下文信息
            **kwargs: 其他评估参数

        Returns:
            CoSTEERMultiFeedback: 包含所有子任务评估结果的多任务反馈对象
                                 每个元素对应一个子任务的聚合反馈

        Example:
            >>> evaluator = CoSTEERMultiEvaluator(single_evaluator, scen=scen)
            >>> feedback = evaluator.evaluate(evo_item)
            >>> # feedback[0] 是第一个子任务的评估结果
            >>> # feedback[1] 是第二个子任务的评估结果

        Note:
            - 使用多进程并行执行，显著提高评估效率
            - 支持多个评估器的同时评估，提供多维度的质量评估
            - 自动处理评估结果的聚合和统计分析
        """
        # 标准化评估器列表，确保始终是列表格式
        eval_l = self.single_evaluator if isinstance(self.single_evaluator, list) else [self.single_evaluator]

        # ==================== 1. 并行评估阶段 ====================
        task_li_feedback_li = []
        # 数据结构说明：
        # task_li_feedback_li: List[List[CoSTEERSingleFeedback]]
        #
        # 结构示例：
        # 假设有2个评估器和3个子任务，每个评估器为每个子任务返回一个CoSTEERSingleFeedback
        # 则task_li_feedback_li的结构为：
        # [
        #   [feedback_1_1, feedback_1_2, feedback_1_3],  # 第1个评估器对所有子任务的评估结果
        #   [feedback_2_1, feedback_2_2, feedback_2_3],  # 第2个评估器对所有子任务的评估结果
        # ]
        # 其中feedback_i_j表示第i个评估器对第j个子任务的评估反馈

        for ev in eval_l:
            # 为每个评估器并行评估所有子任务
            multi_implementation_feedback = multiprocessing_wrapper(
                [
                    (
                        ev.evaluate,  # 评估函数
                        (
                            evo.sub_tasks[index],                                                    # 目标子任务
                            evo.sub_workspace_list[index],                                           # 子任务工作空间
                            evo.sub_gt_implementations[index] if evo.sub_gt_implementations is not None else None,  # 标准实现（可选）
                            queried_knowledge,                                                      # 知识库信息
                        ),
                    )
                    for index in range(len(evo.sub_tasks))  # 遍历所有子任务
                ],
                n=RD_AGENT_SETTINGS.multi_proc_n,  # 使用配置的并行进程数
            )
            task_li_feedback_li.append(multi_implementation_feedback)

        # ==================== 2. 反馈聚合阶段 ====================
        merged_task_feedback = []
        # 沿子任务维度合并多个评估器的反馈
        # task_li_feedback_li[0]是第1个评估器对不同任务的反馈列表

        for task_id, fb in enumerate(task_li_feedback_li[0]):
            # 合并所有评估器对同一子任务的反馈
            # 使用CoSTEERSingleFeedback.merge方法进行智能合并
            fb = fb.merge([fb_li[task_id] for fb_li in task_li_feedback_li])
            merged_task_feedback.append(fb)

        # merged_task_feedback: List[CoSTEERSingleFeedback]
        # 结构示例：
        # [
        #   CoSTEERSingleFeedback(final_decision=True, execution="...", return_checking="...", code="..."),
        #   CoSTEERSingleFeedback(final_decision=False, execution="...", return_checking="...", code="..."),
        #   ...
        # ]
        # 每个元素对应一个子任务在所有评估器上的聚合反馈
        # merged_task_feedback[i]是第i个子任务的聚合反馈

        # ==================== 3. 统计分析阶段 ====================
        final_decision = [
            None if single_feedback is None else single_feedback.final_decision
            for single_feedback in merged_task_feedback
        ]

        # 记录最终决策的统计信息
        logger.info(f"最终决策: {final_decision} 成功数量: {final_decision.count(True)}")

        # TODO: 这是为了兼容factor_implementation的实现
        # 成功的子任务会被标记为已实现
        for index in range(len(evo.sub_tasks)):
            if final_decision[index]:
                evo.sub_tasks[index].factor_implementation = True

        return CoSTEERMultiFeedback(merged_task_feedback)
