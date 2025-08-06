#!/usr/bin/env python3
"""
测试运行器 - 运行所有测试文件
"""

import os
import sys
import subprocess
from pathlib import Path

def find_test_files():
    """查找所有测试文件"""
    test_files = []
    tests_dir = Path(__file__).parent
    
    for py_file in tests_dir.rglob("test_*.py"):
        if py_file.name != "run_tests.py":
            test_files.append(py_file)
    
    return sorted(test_files)

def run_test_file(test_file):
    """运行单个测试文件"""
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            'file': test_file.name,
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'file': test_file.name,
            'success': False,
            'output': '',
            'error': 'Test timed out after 30 seconds'
        }
    except Exception as e:
        return {
            'file': test_file.name,
            'success': False,
            'output': '',
            'error': str(e)
        }

def main():
    """主函数"""
    print("🧪 运行所有测试文件")
    print("=" * 60)
    
    test_files = find_test_files()
    
    if not test_files:
        print("❌ 没有找到测试文件")
        return 1
    
    print(f"📝 找到 {len(test_files)} 个测试文件:")
    for test_file in test_files:
        print(f"   - {test_file.relative_to(Path(__file__).parent)}")
    
    print("\n🏃 开始运行测试...")
    print("-" * 60)
    
    results = []
    for test_file in test_files:
        print(f"\n🔍 运行: {test_file.name}")
        result = run_test_file(test_file)
        results.append(result)
        
        if result['success']:
            print(f"✅ {test_file.name} - 通过")
        else:
            print(f"❌ {test_file.name} - 失败")
            if result['error']:
                print(f"   错误: {result['error'][:200]}{'...' if len(result['error']) > 200 else ''}")
    
    # 统计结果
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print("\n" + "=" * 60)
    print("📊 测试结果统计:")
    print(f"✅ 通过: {passed}/{len(results)}")
    print(f"❌ 失败: {failed}/{len(results)}")
    print(f"📈 成功率: {passed/len(results)*100:.1f}%")
    
    if failed > 0:
        print("\n❌ 失败的测试:")
        for result in results:
            if not result['success']:
                print(f"   - {result['file']}: {result['error']}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())