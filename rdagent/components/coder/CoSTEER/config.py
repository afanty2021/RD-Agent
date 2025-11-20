# -*- coding: utf-8 -*-
"""
CoSTEER 配置系统

本模块定义了CoSTEER框架的所有配置参数，提供：
1. 运行时参数配置
2. 知识库管理配置
3. 查询策略配置
4. 版本兼容性配置

配置说明：
- 支持环境变量覆盖（CoSTEER_前缀）
- 提供默认值确保系统稳定运行
- 支持V1和V2两种知识查询策略
- 灵活的知识库路径配置

作者: RD-Agent Team
"""

from typing import Union

from rdagent.core.conf import ExtendedBaseSettings


class CoSTEERSettings(ExtendedBaseSettings):
    """
    CoSTEER框架配置类

    这是CoSTEER框架的核心配置类，定义了所有运行时参数。
    注意：此类不应直接使用，应通过具体的场景配置类继承使用。

    配置分类：
    - 基础配置：最大循环次数、缓存使用等
    - V1查询配置：历史轨迹、相似成功案例查询
    - V2查询配置：组件级查询、错误处理等
    - 知识库配置：路径、采样策略等

    环境变量支持：
    所有配置项都支持通过环境变量覆盖，格式为：CoSTEER_<配置名>
    例如：export CoSTEER_MAX_LOOP=20
    """

    class Config:
        """Pydantic配置类"""
        env_prefix = "CoSTEER_"
        """环境变量前缀，所有CoSTEER配置项都会使用此前缀"""

    # ==================== 基础运行配置 ====================
    coder_use_cache: bool = False
    """是否使用编码器缓存

    设置为True时，LLM生成的代码会被缓存，相同输入直接返回缓存结果。
    可以显著减少API调用次数，但可能影响代码的多样性和改进。

    建议场景：
    - 开发阶段：设为False，确保代码不断改进
    - 生产阶段：设为True，提高响应速度和稳定性
    """

    max_loop: int = 10
    """最大任务实现循环次数

    限制CoSTEER框架的最大进化迭代次数。
    防止无限循环，确保系统在合理时间内完成。

    调优建议：
    - 复杂任务：可增加到15-20次
    - 简单任务：可减少到5-8次
    - 调试阶段：可设置较高值进行充分探索
    """

    fail_task_trial_limit: int = 20
    """失败任务重试限制

    单个任务的最大失败重试次数。
    超过此限制后，任务将被标记为永久失败。

    设计目的：
    - 避免在困难任务上浪费过多资源
    - 平衡探索深度和系统效率
    """

    # ==================== V1 查询策略配置 ====================
    # V1策略：基于简单相似性和历史轨迹的知识检索

    v1_query_former_trace_limit: int = 3
    """V1策略：历史轨迹查询数量限制

    从当前进化轨迹中查询最近的失败/成功经验数量。
    这些经验有助于理解当前的进展方向和需要避免的问题。

    调优影响：
    - 增加值：提供更多上下文，但可能引入不相关的历史
    - 减少值：聚焦最近经验，但可能遗漏重要模式
    """

    v1_query_similar_success_limit: int = 3
    """V1策略：相似成功案例查询数量限制

    从知识库中查询与当前任务相似的成功案例数量。
    这些案例提供可直接复用的解决方案和最佳实践。

    查询策略：
    - 基于任务描述的embedding相似性
    - 优先选择final_decision=True的案例
    - 考虑代码复杂度和适用场景
    """

    # ==================== V2 查询策略配置 ====================
    # V2策略：基于组件和错误类型的精细化知识检索

    v2_query_component_limit: int = 1
    """V2策略：组件级查询数量限制

    按组件类型（数据加载、特征工程、模型训练等）查询相关知识数量。
    提供更精准的领域特定知识。

    组件分类：
    - DataLoader: 数据加载和预处理组件
    - FeatureEngineer: 特征工程组件
    - ModelTrainer: 模型训练组件
    - Pipeline: 完整流水线组件
    """

    v2_query_error_limit: int = 1
    """V2策略：错误类型查询数量限制

    按错误类型（语法错误、逻辑错误、性能问题等）查询相关解决方案。
    帮助快速定位和修复常见问题。

    错误分类：
    - SyntaxError: 代码语法错误
    - RuntimeError: 运行时错误
    - LogicError: 逻辑错误
    - PerformanceError: 性能问题
    """

    v2_query_former_trace_limit: int = 3
    """V2策略：历史轨迹查询数量限制（与V1相同但算法不同）"""

    v2_add_fail_attempt_to_latest_successful_execution: bool = False
    """V2策略：是否将失败尝试添加到最新成功执行记录中

    设为True时，失败的实现也会被记录在成功执行的上下文中，
    用于分析失败原因和改进方向。

    使用场景：
    - 调试模式：设为True，保留完整探索路径
    - 生产模式：设为False，只记录成功经验
    """

    v2_error_summary: bool = False
    """V2策略：是否生成错误摘要

    设为True时，系统会自动分析和总结错误模式，
    提供结构化的错误诊断和改进建议。

    摘要内容：
    - 错误类型统计
    - 常见失败模式
    - 改进建议和最佳实践
    """

    v2_knowledge_sampler: float = 1.0
    """V2策略：知识采样比例

    控制从知识库中随机采样的比例。
    用于增加知识的多样性，避免总是选择最相似的知识。

    取值范围：
    - 0.0: 总是选择最相似的知识
    - 0.5: 50%概率选择相似知识，50%随机采样
    - 1.0: 完全随机采样

    调优建议：
    - 探索阶段：设置较高值（0.7-1.0）
    - 利用阶段：设置较低值（0.0-0.3）
    """

    # ==================== 知识库配置 ====================
    knowledge_base_path: Union[str, None] = None
    """知识库存储路径

    指定CoSTEER知识库的存储位置。
    支持相对路径和绝对路径。

    路径规范：
    - 相对路径：相对于当前工作目录
    - 绝对路径：完整的文件系统路径
    - None: 使用默认路径（./costeer_knowledge.pkl）

    文件格式：
    - pickle格式：序列化的知识库对象
    - 自动备份：每次保存前自动备份旧版本
    - 版本兼容：支持V1和V2格式的知识库

    环境变量：
    可通过CoSTEER_KNOWLEDGE_BASE_PATH环境变量覆盖
    """
    """Path to the knowledge base"""

    new_knowledge_base_path: Union[str, None] = None
    """Path to the new knowledge base"""

    enable_filelock: bool = False
    filelock_path: Union[str, None] = None

    max_seconds_multiplier: int = 10**6


CoSTEER_SETTINGS = CoSTEERSettings()
