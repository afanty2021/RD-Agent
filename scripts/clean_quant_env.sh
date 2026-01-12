#!/bin/bash
# Qlib环境清理脚本
# 用于清理残留的Python进程和临时文件

echo "🔍 开始清理Qlib运行环境..."

# 1. 查找并杀死残留的rdagent进程
echo "📌 清理残留的rdagent进程..."
pkill -f "rdagent" 2>/dev/null || echo "✅ 没有残留的rdagent进程"

# 2. 清理joblib内存映射文件夹
echo "📌 清理joblib临时文件..."
rm -rf /var/folders/*/T/joblib_memmapping_folder_* 2>/dev/null || echo "✅ 没有残留的joblib临时文件"

# 3. 清理Python缓存
echo "📌 清理Python缓存..."
find /Users/berton/Github/RD-Agent -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || echo "✅ 没有Python缓存需要清理"

# 4. 显示当前Python进程
echo ""
echo "📊 当前运行的Python进程："
ps aux | grep -i "[p]ython" | grep -v grep || echo "✅ 没有Python进程在运行"

echo ""
echo "✅ 环境清理完成！"
echo ""
echo "💡 建议："
echo "1. 使用新的配置文件 conf_baseline_factors_model_fixed.yaml"
echo "2. 如果问题仍然存在，尝试重启终端"
echo "3. 考虑使用更小的时间范围或更少的特征进行测试"
