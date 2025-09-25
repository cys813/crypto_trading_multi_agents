# 加密货币交易系统开发命令

## 环境设置命令
```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装完整依赖
pip install -r requirements_full.txt

# 安装Web相关依赖
pip install -r requirements_web.txt
```

## 代码质量检查命令
```bash
# 代码格式化
black src/
black .

# 代码排序
isort src/
isort .

# 代码静态检查
flake8 src/
flake8 .

# 类型检查
mypy src/
mypy .
```

## 测试命令
```bash
# 运行所有测试
pytest tests/

# 运行带覆盖率的测试
pytest tests/ --cov=src/

# 详细测试输出
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_market_analysis.py
```

## 系统运行命令
```bash
# 启动Web界面
python start_web.py

# 测试系统模块
python test_system_modules.py

# 验证辩论器实现
python verify_debator_simple.py

# 验证辩论器AI修改
python verify_debators_ai_modification.py

# 验证辩论器集成
python verify_debator_integration.py

# 验证对偶性修复
python verify_duality_fix.py

# 验证DeFi实现
python verify_defi_implementation.py

# 测试简单辩论器
python test_debator_simple.py

# 测试研究员对偶性
python test_researcher_duality.py

# 测试完整DeFi功能
python test_defi_complete.py

# 测试ETH DeFi简单功能
python test_eth_defi_simple.py

# 分析ETH DeFi
python analyze_eth_defi.py

# ETH DeFi分析演示
python eth_defi_analysis_demo.py
```

## 系统测试命令
```bash
# 运行系统测试（会生成测试结果文件）
python test_system_modules.py
```

## 数据分析命令
```bash
# 查看系统测试结果
cat system_test_results_*.json

# 分析特定的测试结果
cat system_test_results_20250813_130140.json
```

## 项目管理命令
```bash
# 查看项目结构
tree .    # 需要安装tree
ls -la

# 查看Python文件
find . -name "*.py" | head -10

# 查看配置文件
cat config.json
cat requirements.txt
```

## Git操作命令
```bash
# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Initial commit"

# 查看状态
git status

# 查看差异
git diff

# 查看日志
git log --oneline
```

## 实用命令
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 退出虚拟环境
deactivate

# 查看Python版本
python --version

# 查看已安装的包
pip list

# 查看包信息
pip show <package_name>

# 升级pip
pip install --upgrade pip
```

## 调试命令
```bash
# 启动Python调试器
python -m pdb start_web.py

# 或使用ipdb（如果安装）
python -m ipdb start_web.py

# 查看Python路径
python -c "import sys; print(sys.path)"

# 检查模块导入
python -c "import <module_name>; print('Module imported successfully')"
```

## 日志查看命令
```bash
# 查看实时日志
tail -f logs/trading_system.log

# 查看错误日志
grep ERROR logs/trading_system.log

# 查看特定时间段的日志
grep "2025-08-15" logs/trading_system.log
```

## 系统监控命令
```bash
# 查看系统资源使用
htop
# 或
top

# 查看磁盘使用
df -h

# 查看内存使用
free -h

# 查看网络连接
netstat -tulpn
```

## 注意事项
1. 所有命令都应该在项目根目录下运行
2. 运行测试前确保所有依赖已安装
3. 代码提交前运行质量检查命令
4. 定期备份重要的配置文件和数据