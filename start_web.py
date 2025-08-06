#!/usr/bin/env python3
"""
启动加密货币交易Web界面
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动Web应用"""
    
    print("🚀 启动 Crypto Trading Agents Web 界面...")
    
    # 检查必要的目录
    directories = [
        Path.home() / ".crypto_trading_agents",
        Path.home() / ".crypto_trading_agents" / "progress",
        Path.home() / ".crypto_trading_agents" / "sessions"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")
    
    # 检查依赖
    try:
        import streamlit
        print(f"✅ Streamlit 版本: {streamlit.__version__}")
    except ImportError:
        print("❌ 请安装 Streamlit: pip install streamlit")
        return
    
    # 启动Web应用
    try:
        import streamlit.web.cli as stcli
        import sys
        
        print("🌐 正在启动Web服务器...")
        print("📍 Web界面将在浏览器中自动打开")
        print("🔗 如果没有自动打开，请访问: http://localhost:8501")
        print("⏹️  按 Ctrl+C 停止服务器")
        
        # 启动Streamlit
        sys.argv = [
            "streamlit",
            "run",
            str(project_root / "src" / "web" / "app.py"),
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--server.fileWatcherType=none",
            "--browser.gatherUsageStats=false"
        ]
        
        stcli.main()
        
    except KeyboardInterrupt:
        print("\n🛑 Web服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()