# -*- coding: utf-8 -*-
"""
RD-Agent 评估框架核心模块

本模块定义了RD-Agent系统的评估基础设施，提供：
1. 反馈信息的统一表示和处理
2. 可评估对象的抽象定义
3. 评估器的接口规范

该模块被设计为可在不同框架间共享的通用评估组件。

作者: RD-Agent Team
"""

from abc import ABC, abstractmethod


class Feedback:
    """
    反馈信息基类

    设计原则：
    - 主要作为数据类使用，存储评估结果和相关信息
    - 反馈信息的构建过程应该在评估器中完成
    - 提供多种状态判断方法，支持复杂的评估逻辑

    反馈信息包含执行结果、性能指标、错误信息等评估相关数据。
    """

    def is_acceptable(self) -> bool:
        """
        判断解决方案是否可接受

        有时候解决方案已经达到可接受的标准，但我们仍希望进一步优化。
        因此使用不同的逻辑来判断解决方案是可接受的还是已完成的。

        Returns:
            bool: 如果解决方案可接受则返回True，否则返回False
        """
        return self.__bool__()

    def finished(self) -> bool:
        """
        判断任务是否已完成

        在某些实现中，任务可能失败多次，导致智能体跳过实现。
        因此跳过和成功都表示任务已完成。

        Returns:
            bool: 如果任务已完成（成功或跳过）则返回True，否则返回False
        """
        return self.__bool__()

    def __bool__(self) -> bool:
        """
        布尔值转换，默认返回True

        子类应该重写此方法来实现具体的判断逻辑。

        Returns:
            bool: 默认返回True，表示反馈是积极的
        """
        return True


class EvaluableObj:
    """
    可评估对象抽象基类

    定义了一组可评估的信息集合，可以包含：
    - 任务描述和需求
    - 解决方案代码或配置
    - 基准真相或预期结果
    - 执行环境信息

    任何需要被评估的对象都应该继承此类。
    """


class Evaluator(ABC):
    """
    评估器抽象基类

    设计原则：
    - 覆盖从原始信息构建反馈的完整过程
    - 反馈构建通常分为两个阶段：
      1. 原始信息收集（标准输出、工作空间状态等）
      2. 高级/汇总反馈信息处理

    所有具体的评估器实现都需要继承此类。
    """

    @abstractmethod
    def evaluate(
        self,
        eo: EvaluableObj,
    ) -> Feedback:
        """
        评估可评估对象并生成反馈

        Args:
            eo: 需要评估的可评估对象

        Returns:
            Feedback: 包含评估结果和相关信息的反馈对象

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError
