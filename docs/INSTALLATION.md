# 安装指南

## 📋 系统要求

### 操作系统
- **推荐**: Linux, macOS, Windows 10+
- **内存**: 最少 4GB RAM，推荐 8GB+
- **存储**: 最少 1GB 可用空间
- **网络**: 稳定的互联网连接

### 软件依赖
- **Python**: 3.8 或更高版本
- **pip**: Python包管理器
- **Git**: 版本控制工具

## 🚀 快速安装

### 步骤 1: 获取项目代码

```bash
# 克隆项目
git clone <repository-url>
cd crypto_trading_agents

# 或者下载ZIP文件并解压
```

### 步骤 2: 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv crypto_env

# 激活虚拟环境
# Windows:
crypto_env\Scripts\activate
# macOS/Linux:
source crypto_env/bin/activate
```

### 步骤 3: 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装Web界面依赖
pip install -r requirements_web.txt
```

### 步骤 4: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
nano .env  # 或使用其他编辑器
```

### 步骤 5: 启动应用

```bash
# 启动Web界面
python start_web.py
```

## 🔧 详细配置

### Python环境配置

#### 检查Python版本
```bash
python --version
# 或
python3 --version
```

#### 升级pip
```bash
python -m pip install --upgrade pip
```

### 环境变量配置

编辑 `.env` 文件：

```env
# 基础配置
DEBUG=false
VERBOSE=false

# LLM提供商配置
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 加密货币交易所配置
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# 数据源配置
COINGECKO_API_KEY=your_coingecko_api_key_here
GLASSNODE_API_KEY=your_glassnode_api_key_here
```

### 数据目录创建

```bash
# 创建必要的数据目录
mkdir -p data/analysis
mkdir -p data/sessions
mkdir -p data/config
mkdir -p ~/.crypto_trading_agents/progress
mkdir -p ~/.crypto_trading_agents/sessions
```

## 📦 依赖包说明

### 基础依赖 (requirements.txt)

```
# 核心框架
streamlit>=1.28.0
python-dotenv>=1.0.0

# AI模型
openai>=1.0.0
dashscope>=1.13.6

# 数据处理
pandas>=1.5.0
numpy>=1.21.0
requests>=2.28.0

# 加密货币
ccxt>=4.0.0

# 可视化
plotly>=5.15.0
matplotlib>=3.5.0

# 工具
python-dateutil>=2.8.0
pytz>=2022.1
```

### Web界面依赖 (requirements_web.txt)

```
# Web界面
streamlit>=1.28.0
python-dotenv>=1.0.0

# AI和数据处理
openai>=1.0.0
dashscope>=1.13.6
pandas>=1.5.0
numpy>=1.21.0
requests>=2.28.0
ccxt>=4.0.0
plotly>=5.15.0
matplotlib>=3.5.0
python-dateutil>=2.8.0
pytz>=2022.1
```

## 🔍 可选配置

### Docker安装（推荐）

```bash
# 构建Docker镜像
docker build -t crypto-trading-agents .

# 运行容器
docker run -p 8501:8501 -v $(pwd)/data:/app/data crypto-trading-agents
```

### 系统服务安装

#### Linux (systemd)
```bash
# 创建服务文件
sudo nano /etc/systemd/system/crypto-trading-agents.service
```

```ini
[Unit]
Description=Crypto Trading Agents Web Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/crypto_trading_agents
Environment=PATH=/path/to/crypto_env/bin
ExecStart=/path/to/crypto_env/bin/python start_web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable crypto-trading-agents
sudo systemctl start crypto-trading-agents
```

#### Windows (服务)
使用NSSM (Non-Sucking Service Manager):

```bash
# 下载NSSM
# 安装服务
nssm install "Crypto Trading Agents" "C:\path\to\crypto_env\python.exe" "C:\path\to\start_web.py"

# 启动服务
nssm start "Crypto Trading Agents"
```

## 🧪 测试安装

### 测试基础功能
```bash
# 运行测试
python -m pytest tests/

# 或运行简单的导入测试
python -c "import streamlit; print('Streamlit OK')"
python -c "import ccxt; print('CCXT OK')"
python -c "import pandas; print('Pandas OK')"
```

### 测试Web界面
```bash
# 启动Web服务器
python start_web.py

# 在浏览器中访问
# http://localhost:8501
```

## 🔧 故障排除

### 常见问题

#### Python版本问题
```bash
# 检查Python版本
python --version

# 如果版本过低，升级Python
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9

# macOS (使用Homebrew)
brew install python@3.9

# Windows
# 从https://python.org下载最新版本
```

#### 权限问题
```bash
# Linux/macOS权限问题
chmod +x start_web.py
chmod 755 scripts/*.sh

# Windows权限问题
# 以管理员身份运行命令提示符
```

#### 端口占用问题
```bash
# 检查端口占用
netstat -an | grep 8501

# 更改端口
export STREAMLIT_SERVER_PORT=8502
python start_web.py
```

#### 依赖安装失败
```bash
# 清理pip缓存
pip cache purge

# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 或使用阿里云镜像
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

### 网络问题

#### 代理设置
```bash
# 设置代理
export HTTP_PROXY=http://proxy-server:port
export HTTPS_PROXY=http://proxy-server:port

# 或使用pip代理
pip install --proxy=http://proxy-server:port -r requirements.txt
```

#### 防火墙设置
```bash
# Linux (ufw)
sudo ufw allow 8501

# Windows防火墙
# 控制面板 -> 系统和安全 -> Windows Defender防火墙
# 添加入站规则，端口8501
```

## 📚 相关资源

### 官方文档
- [Python官方文档](https://docs.python.org/)
- [Streamlit官方文档](https://docs.streamlit.io/)
- [CCXT官方文档](https://ccxt.readthedocs.io/)

### 社区支持
- [Stack Overflow](https://stackoverflow.com/)
- [GitHub Issues](https://github.com/streamlit/streamlit/issues)
- [Reddit r/Python](https://www.reddit.com/r/Python/)

### 视频教程
- [YouTube: Streamlit教程](https://www.youtube.com/c/Streamlit)
- [B站: Python教程](https://www.bilibili.com/)

---

## 🎉 安装完成！

安装完成后，您可以：

1. **启动Web界面**: `python start_web.py`
2. **访问应用**: `http://localhost:8501`
3. **配置API密钥**: 编辑 `.env` 文件
4. **开始分析**: 选择交易对并运行分析

如果遇到问题，请查看故障排除部分或提交Issue。