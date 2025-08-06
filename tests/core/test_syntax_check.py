#!/usr/bin/env python3
"""
语法检查测试
"""

import sys
import os
import ast

def check_syntax(file_path):
    """检查Python文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    print("检查技术分析师代码语法...")
    
    files_to_check = [
        "crypto_trading_agents/crypto_trading_agents/agents/analysts/technical_analyst.py",
        "crypto_trading_agents/crypto_trading_agents/agents/analysts/ai_technical_analyzer.py"
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            is_valid, error = check_syntax(file_path)
            if is_valid:
                print(f"✅ {file_path} - 语法正确")
            else:
                print(f"❌ {file_path} - 语法错误: {error}")
                all_good = False
        else:
            print(f"⚠️  {file_path} - 文件不存在")
            all_good = False
    
    if all_good:
        print("\n🎉 所有文件语法检查通过!")
    else:
        print("\n⚠️  存在语法错误，请修复")

if __name__ == "__main__":
    main()