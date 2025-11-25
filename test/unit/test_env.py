"""
环境工具模块单元测试

测试 QlibCondaEnv 类的功能
"""

import pytest
from rdagent.utils.env import QlibCondaEnv


def test_prepare_env_not_created():
    """测试当conda环境未创建时的准备"""
    env = QlibCondaEnv("nonexistent_env", "test_env")
    result = env.prepare()

    assert not result, "环境不存在时应该返回False"
    print(f"✅ 测试通过: 不存在的环境准备返回False")


def test_prepare_env_already_exists():
    """测试当conda环境已存在时的准备"""
    env = QlibCondaEnv("test_env")
    result = env.prepare()

    assert result, "环境已存在时应该返回True"
    print(f"✅ 测试通过: 已存在的环境准备返回True")


def test_prepare_env_with_conda_path():
    """测试指定conda路径时的环境准备"""
    env = QlibCondaEnv("test_env", conda_path="/custom/conda")
    result = env.prepare()

    assert result, "指定conda路径时应该能正常准备"
    print(f"✅ 测试通过: 指定conda路径的环境准备返回True")


def test_change_bin_path():
    """测试二进制路径修改"""
    env = QlibCondaEnv("test_env")
    result = env.change_bin_path("/new/python")

    # 验证二进制路径是否正确修改
    assert "python" in env.bin_path, "二进制路径应该包含新的python"
    print(f"✅ 测试通过: 二进制路径修改为'{env.bin_path}'")


def test_get_conda_info():
    """测试获取conda环境信息"""
    env = QlibCondaEnv("test_env")
    conda_info = env.get_conda_info()

    assert conda_info is not None, "应该能获取conda环境信息"
    assert "env_name" in conda_info, "conda信息应包含环境名"
    print(f"✅ 测试通过: 获取到conda环境信息")


if __name__ == "__main__":
    # 运行所有测试
    test_prepare_env_not_created()
    test_prepare_env_already_exists()
    test_prepare_env_with_conda_path()
    test_change_bin_path()
    test_get_conda_info()

    print("\n🧪 所有环境工具测试通过!")