#!/usr/bin/env python3
"""
Qlib环境诊断脚本
用于检查系统配置和潜在的兼容性问题
"""

import sys
import os
import subprocess
from typing import List, Tuple

def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return True, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_python_version():
    """检查Python版本"""
    print("🐍 Python版本检查")
    print(f"   当前版本: {sys.version}")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print("   ✅ Python版本兼容")
        return True
    else:
        print("   ⚠️ 建议使用Python 3.9+")
        return False

def check_pytorch():
    """检查PyTorch配置"""
    print("\n🔥 PyTorch配置检查")
    try:
        import torch
        print(f"   PyTorch版本: {torch.__version__}")
        print(f"   CUDA可用: {torch.cuda.is_available()}")
        if hasattr(torch.backends, 'mps'):
            print(f"   MPS可用: {torch.backends.mps.is_available()}")
        print("   ✅ PyTorch安装正常")
        return True
    except ImportError as e:
        print(f"   ❌ PyTorch导入失败: {e}")
        return False

def check_qlib():
    """检查Qlib配置"""
    print("\n💰 Qlib配置检查")
    try:
        import qlib
        print(f"   Qlib版本: {qlib.__version__}")
        print("   ✅ Qlib安装正常")
        return True
    except ImportError as e:
        print(f"   ❌ Qlib导入失败: {e}")
        return False

def check_joblib():
    """检查Joblib配置"""
    print("\n⚙️ Joblib配置检查")
    try:
        import joblib
        print(f"   Joblib版本: {joblib.__version__}")
        print(f"   临时目录: {joblib.disk_partitions() if hasattr(joblib, 'disk_partitions') else 'N/A'}")
        print("   ✅ Joblib安装正常")
        return True
    except ImportError as e:
        print(f"   ❌ Joblib导入失败: {e}")
        return False

def check_environment_variables():
    """检查环境变量"""
    print("\n🔧 环境变量检查")
    env_vars = [
        'OMP_NUM_THREADS',
        'MKL_NUM_THREADS',
        'PYTORCH_ENABLE_MPS_FALLBACK',
        'JOBLIB_START_METHOD'
    ]
    all_set = True
    for var in env_vars:
        value = os.environ.get(var, '未设置')
        status = "✅" if value != '未设置' else "⚠️"
        print(f"   {status} {var}: {value}")
        if value == '未设置':
            all_set = False
    if all_set:
        print("   ✅ 所有推荐环境变量已设置")
    else:
        print("   ⚠️ 部分环境变量未设置，可能影响性能")
    return all_set

def check_system_resources():
    """检查系统资源"""
    print("\n💻 系统资源检查")

    # 内存检查
    try:
        import psutil
        mem = psutil.virtual_memory()
        print(f"   总内存: {mem.total / (1024**3):.2f} GB")
        print(f"   可用内存: {mem.available / (1024**3):.2f} GB")
        print(f"   内存使用率: {mem.percent:.1f}%")
        if mem.available < 2 * 1024**3:  # 小于2GB
            print("   ⚠️ 可用内存不足，建议关闭其他应用")
            return False
        else:
            print("   ✅ 内存充足")
            return True
    except ImportError:
        print("   ⚠️ psutil未安装，跳过内存检查")
        return True

def check_residual_processes():
    """检查残留进程"""
    print("\n🔍 残留进程检查")
    success, output = run_command(['ps', 'aux'])
    if success:
        python_procs = [line for line in output.split('\n') if 'python' in line.lower() and 'rdagent' in line.lower()]
        if python_procs:
            print(f"   ⚠️ 发现{len(python_procs)}个残留的rdagent进程")
            for proc in python_procs[:3]:
                print(f"      {proc}")
            return False
        else:
            print("   ✅ 没有残留的rdagent进程")
            return True
    else:
        print("   ⚠️ 无法检查进程")
        return True

def check_temp_files():
    """检查临时文件"""
    print("\n🗑️ 临时文件检查")
    import tempfile
    temp_dir = tempfile.gettempdir()

    try:
        joblib_dirs = [d for d in os.listdir(temp_dir) if 'joblib' in d]
        if joblib_dirs:
            print(f"   ⚠️ 发现{len(joblib_dirs)}个joblib临时目录")
            return False
        else:
            print("   ✅ 没有残留的临时文件")
            return True
    except Exception as e:
        print(f"   ⚠️ 无法检查临时文件: {e}")
        return True

def main():
    """主函数"""
    print("=" * 60)
    print("🔬 Qlib环境诊断工具")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_pytorch(),
        check_qlib(),
        check_joblib(),
        check_environment_variables(),
        check_system_resources(),
        check_residual_processes(),
        check_temp_files()
    ]

    print("\n" + "=" * 60)
    print("📊 诊断总结")
    print("=" * 60)
    passed = sum(checks)
    total = len(checks)
    print(f"   通过检查: {passed}/{total}")

    if passed == total:
        print("   ✅ 所有检查通过，环境配置良好！")
        return 0
    elif passed >= total * 0.7:
        print("   ⚠️ 部分检查未通过，建议修复后再运行训练")
        return 1
    else:
        print("   ❌ 多项检查未通过，存在严重配置问题")
        return 2

if __name__ == "__main__":
    sys.exit(main())
