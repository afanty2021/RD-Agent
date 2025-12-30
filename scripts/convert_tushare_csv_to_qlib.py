#!/usr/bin/env python3
"""
Tushare CSV 数据转换为 Qlib 二进制格式

将 ~/.qlib/qlib_data/cn_data/stock_data/ 下的 Tushare CSV 文件
转换为 Qlib 专用的二进制格式。

使用方法:
    python scripts/convert_tushare_csv_to_qlib.py

数据流程:
    Tushare CSV → Qlib .bin 格式 → RD-Agent 使用
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 添加 Qlib 路径
qlib_path = Path(__file__).parent.parent / "qlib"
if qlib_path.exists():
    sys.path.insert(0, str(qlib_path))

# 添加当前项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def backup_existing_data():
    """备份现有 Qlib 数据"""
    qlib_data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    backup_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data_backup"

    if qlib_data_dir.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(str(backup_dir) + f"_{timestamp}")

        print(f"📦 备份现有 Qlib 数据到: {backup_path}")
        try:
            shutil.copytree(qlib_data_dir, backup_path)
            print(f"✅ 备份完成")
            return backup_path
        except Exception as e:
            print(f"⚠️  备份失败: {e}")
            return None
    else:
        print("ℹ️  没有需要备份的数据")
        return None


def get_csv_files_count(csv_dir: Path) -> int:
    """统计 CSV 文件数量"""
    csv_files = list(csv_dir.glob("*.csv"))
    return len(csv_files)


def convert_csv_to_qlib(
    csv_dir: Path,
    qlib_dir: Path,
    date_field: str = "trade_date",
    symbol_field: str = "ts_code"
):
    """
    使用 Qlib dump_bin.py 将 CSV 转换为二进制格式

    参数:
        csv_dir: Tushare CSV 文件目录
        qlib_dir: Qlib 数据输出目录
        date_field: 日期字段名
        symbol_field: 股票代码字段名
    """
    print(f"\n🔄 开始转换数据...")
    print(f"   源目录: {csv_dir}")
    print(f"   目标目录: {qlib_dir}")
    print(f"   CSV 文件数: {get_csv_files_count(csv_dir)}")

    # 导入 Qlib 的 dump_bin 模块
    try:
        from qlib.scripts.dump_bin import DumpDataAll

        # 创建输出目录
        qlib_dir.mkdir(parents=True, exist_ok=True)

        # 执行转换
        # csv_dir 格式: ~/.qlib/qlib_data/cn_data/stock_data
        # qlib_dir 格式: ~/.qlib/qlib_data/cn_data
        dumper = DumpDataAll(
            data_path=str(csv_dir),
            qlib_dir=str(qlib_dir),
            freq="day",
            max_workers=16,  # 并行处理
            date_field_name=date_field,
            file_suffix=".csv",
            symbol_field_name=symbol_field,
        )

        print("\n⚙️  正在转换...")
        dumper.dump()

        print("\n✅ 转换完成！")
        return True

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        print("   请确保 Qlib 已正确安装")
        return False
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_conversion(qlib_dir: Path):
    """验证转换结果"""
    print("\n🔍 验证转换结果...")

    # 检查必需的目录
    required_dirs = ["calendars", "features", "instruments"]
    all_exist = True

    for dir_name in required_dirs:
        dir_path = qlib_dir / dir_name
        if dir_path.exists():
            if dir_name == "calendars":
                calendar_files = list(dir_path.glob("*.txt"))
                print(f"   ✅ {dir_name}/: {len(calendar_files)} 个文件")
            elif dir_name == "features":
                # 统计股票数量
                stock_dirs = [d for d in dir_path.iterdir() if d.is_dir()]
                print(f"   ✅ {dir_name}/: {len(stock_dirs)} 只股票")
            elif dir_name == "instruments":
                instrument_files = list(dir_path.glob("*.txt"))
                print(f"   ✅ {dir_name}/: {len(instrument_files)} 个文件")
        else:
            print(f"   ❌ {dir_name}/: 目录不存在")
            all_exist = False

    # 检查 features 目录下的二进制文件
    features_dir = qlib_dir / "features"
    if features_dir.exists():
        bin_files = list(features_dir.rglob("*.bin"))
        print(f"   📊 二进制文件: {len(bin_files)} 个")

        if bin_files:
            # 显示部分示例
            print(f"   示例文件:")
            for f in bin_files[:5]:
                size_kb = f.stat().st_size / 1024
                print(f"     - {f.relative_to(qlib_dir)} ({size_kb:.1f} KB)")

    return all_exist


def regenerate_rdagent_data():
    """重新生成 RD-Agent 的数据文件夹"""
    print("\n🔄 重新生成 RD-Agent 数据文件夹...")

    try:
        from rdagent.scenarios.qlib.experiment.utils import generate_data_folder_from_qlib

        generate_data_folder_from_qlib()
        print("✅ RD-Agent 数据文件夹已更新")
        return True

    except Exception as e:
        print(f"⚠️  RD-Agent 数据文件夹更新失败: {e}")
        print("   这不是关键问题，RD-Agent 会在下次运行时自动生成")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Tushare CSV → Qlib 二进制格式转换")
    print("=" * 60)

    # 定义路径
    csv_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data" / "stock_data"
    qlib_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"

    # 检查源目录
    if not csv_dir.exists():
        print(f"\n❌ 源目录不存在: {csv_dir}")
        print("   请确保 Tushare CSV 数据已下载到该目录")
        return 1

    csv_count = get_csv_files_count(csv_dir)
    print(f"\n📊 源数据统计:")
    print(f"   CSV 文件数量: {csv_count}")

    if csv_count == 0:
        print(f"\n❌ 源目录中没有 CSV 文件")
        return 1

    # 询问是否备份
    print(f"\n⚠️  警告: 转换过程将覆盖现有的 Qlib 二进制数据")
    response = input("是否备份现有数据？(y/n): ").strip().lower()

    if response == 'y':
        backup_path = backup_existing_data()
        if backup_path:
            print(f"   如需恢复，请执行:")
            print(f"   rm -rf {qlib_dir}")
            print(f"   mv {backup_path} {qlib_dir}")

    # 执行转换
    success = convert_csv_to_qlib(csv_dir, qlib_dir)

    if not success:
        print("\n❌ 转换失败，请检查错误信息")
        return 1

    # 验证结果
    if not validate_conversion(qlib_dir):
        print("\n⚠️  转换验证失败")
        return 1

    # 询问是否重新生成 RD-Agent 数据
    print(f"\n❓ 是否重新生成 RD-Agent 数据文件夹？")
    print(f"   这将更新 RD-Agent 使用的 HDF5 数据文件")
    response = input("重新生成？(y/n): ").strip().lower()

    if response == 'y':
        regenerate_rdagent_data()

    print("\n" + "=" * 60)
    print("🎉 转换流程完成！")
    print("=" * 60)
    print("\n📝 后续步骤:")
    print("   1. 检查 Qlib 数据目录:")
    print(f"      ls -la {qlib_dir}/features/")
    print("   2. 如果 RD-Agent 正在运行，重启它以使用新数据")
    print("   3. 或者在下次运行 RD-Agent 时，它会自动使用新数据")

    return 0


if __name__ == "__main__":
    sys.exit(main())
