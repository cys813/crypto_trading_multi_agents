#!/usr/bin/env python3
"""
加密货币交易代理系统模块调用测试文件
用于调试和测试系统各个模块的功能
"""

import sys
import os
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.crypto_trading_agents.graph.crypto_trading_graph import CryptoTradingGraph
from src.crypto_trading_agents.unified_config import get_unified_config
from src.crypto_trading_agents.default_config import get_config


class SystemModuleTester:
    """系统模块测试器"""
    
    def __init__(self):
        self.config = None
        self.trading_graph = None
        self.test_results = {}
        
    def setup_config(self) -> bool:
        """设置配置"""
        try:
            print("🔧 正在初始化配置...")
            
            # 获取统一配置
            self.config = get_unified_config()
            
            print("✅ 配置初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 配置初始化失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def setup_trading_graph(self) -> bool:
        """设置交易图"""
        try:
            print("🔧 正在初始化交易图...")
            
            if not self.config:
                print("❌ 配置未初始化")
                return False
            
            # 创建交易图实例
            self.trading_graph = CryptoTradingGraph(
                config=self.config,
                debug=True
            )
            
            print("✅ 交易图初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 交易图初始化失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_analysts(self) -> bool:
        """测试分析师模块"""
        try:
            print("🔍 开始测试分析师模块...")
            
            if not self.trading_graph:
                print("❌ 交易图未初始化")
                return False
            
            # 测试各个分析师
            analysts = {
                "technical_analyst": self.trading_graph.technical_analyst,
                "onchain_analyst": self.trading_graph.onchain_analyst,
                "sentiment_analyst": self.trading_graph.sentiment_analyst,
                "market_maker_analyst": self.trading_graph.market_maker_analyst,
                "defi_analyst": self.trading_graph.defi_analyst
            }
            
            analyst_results = {}
            
            for analyst_name, analyst in analysts.items():
                print(f"  📊 测试 {analyst_name}...")
                
                try:
                    # 测试分析师基本信息
                    if hasattr(analyst, 'name'):
                        print(f"    名称: {analyst.name}")
                    
                    if hasattr(analyst, 'description'):
                        print(f"    描述: {analyst.description}")
                    
                    # 测试分析方法
                    if hasattr(analyst, 'analyze_with_ai_enhancement'):
                        print(f"    ✅ 支持AI增强分析")
                    else:
                        print(f"    ⚠️  不支持AI增强分析")
                    
                    analyst_results[analyst_name] = {
                        "status": "success",
                        "name": getattr(analyst, 'name', analyst_name),
                        "has_ai_enhancement": hasattr(analyst, 'analyze_with_ai_enhancement')
                    }
                    
                except Exception as e:
                    print(f"    ❌ 测试失败: {str(e)}")
                    analyst_results[analyst_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            self.test_results["analysts"] = analyst_results
            print("✅ 分析师模块测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 分析师模块测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_researchers(self) -> bool:
        """测试研究员模块"""
        try:
            print("🔍 开始测试研究员模块...")
            
            if not self.trading_graph:
                print("❌ 交易图未初始化")
                return False
            
            # 测试各个研究员
            researchers = {
                "bull_researcher": self.trading_graph.bull_researcher,
                "bear_researcher": self.trading_graph.bear_researcher,
                "research_manager": self.trading_graph.research_manager
            }
            
            researcher_results = {}
            
            for researcher_name, researcher in researchers.items():
                print(f"  🔬 测试 {researcher_name}...")
                
                try:
                    # 测试研究员基本信息
                    if hasattr(researcher, 'name'):
                        print(f"    名称: {researcher.name}")
                    
                    if hasattr(researcher, 'description'):
                        print(f"    描述: {researcher.description}")
                    
                    # 测试研究方法
                    if hasattr(researcher, 'conduct_research'):
                        print(f"    ✅ 支持研究方法")
                    else:
                        print(f"    ⚠️  不支持研究方法")
                    
                    researcher_results[researcher_name] = {
                        "status": "success",
                        "name": getattr(researcher, 'name', researcher_name),
                        "has_research_method": hasattr(researcher, 'conduct_research')
                    }
                    
                except Exception as e:
                    print(f"    ❌ 测试失败: {str(e)}")
                    researcher_results[researcher_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            self.test_results["researchers"] = researcher_results
            print("✅ 研究员模块测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 研究员模块测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_risk_managers(self) -> bool:
        """测试风险管理模块"""
        try:
            print("🔍 开始测试风险管理模块...")
            
            if not self.trading_graph:
                print("❌ 交易图未初始化")
                return False
            
            # 测试风险管理模块
            risk_managers = {
                "crypto_risk_manager": self.trading_graph.crypto_risk_manager,
                "conservative_debator": self.trading_graph.conservative_debator,
                "neutral_debator": self.trading_graph.neutral_debator,
                "aggressive_debator": self.trading_graph.aggressive_debator
            }
            
            risk_manager_results = {}
            
            for manager_name, manager in risk_managers.items():
                print(f"  🛡️  测试 {manager_name}...")
                
                try:
                    # 测试风险管理器基本信息
                    if hasattr(manager, 'name'):
                        print(f"    名称: {manager.name}")
                    
                    if hasattr(manager, 'description'):
                        print(f"    描述: {manager.description}")
                    
                    # 测试风险管理方法
                    if hasattr(manager, 'assess_risk'):
                        print(f"    ✅ 支持风险评估")
                    else:
                        print(f"    ⚠️  不支持风险评估")
                    
                    risk_manager_results[manager_name] = {
                        "status": "success",
                        "name": getattr(manager, 'name', manager_name),
                        "has_risk_assessment": hasattr(manager, 'assess_risk')
                    }
                    
                except Exception as e:
                    print(f"    ❌ 测试失败: {str(e)}")
                    risk_manager_results[manager_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            self.test_results["risk_managers"] = risk_manager_results
            print("✅ 风险管理模块测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 风险管理模块测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_trader(self) -> bool:
        """测试交易员模块"""
        try:
            print("🔍 开始测试交易员模块...")
            
            if not self.trading_graph:
                print("❌ 交易图未初始化")
                return False
            
            trader = self.trading_graph.crypto_trader
            
            print(f"  📈 测试 crypto_trader...")
            
            try:
                # 测试交易员基本信息
                if hasattr(trader, 'name'):
                    print(f"    名称: {trader.name}")
                
                if hasattr(trader, 'description'):
                    print(f"    描述: {trader.description}")
                
                # 测试交易方法
                if hasattr(trader, 'make_trading_decision'):
                    print(f"    ✅ 支持交易决策")
                else:
                    print(f"    ⚠️  不支持交易决策")
                
                self.test_results["trader"] = {
                    "status": "success",
                    "name": getattr(trader, 'name', 'crypto_trader'),
                    "has_trading_decision": hasattr(trader, 'make_trading_decision')
                }
                
                print("✅ 交易员模块测试完成")
                return True
                
            except Exception as e:
                print(f"    ❌ 测试失败: {str(e)}")
                self.test_results["trader"] = {
                    "status": "failed",
                    "error": str(e)
                }
                return False
            
        except Exception as e:
            print(f"❌ 交易员模块测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_analysis_workflow(self, symbol: str = "BTC/USDT") -> bool:
        """测试完整分析流程"""
        try:
            print(f"🔄 开始测试完整分析流程 ({symbol})...")
            
            if not self.trading_graph:
                print("❌ 交易图未初始化")
                return False
            
            # 准备测试数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            print(f"  📅 分析时间范围: {start_date} 到 {end_date}")
            
            # 执行分析
            try:
                result = self.trading_graph.propagate(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                print(f"  ✅ 分析完成")
                print(f"  📊 分析结果键: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                
                self.test_results["analysis_workflow"] = {
                    "status": "success",
                    "symbol": symbol,
                    "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                    "result_type": type(result).__name__
                }
                
                return True
                
            except Exception as e:
                print(f"  ❌ 分析失败: {str(e)}")
                self.test_results["analysis_workflow"] = {
                    "status": "failed",
                    "symbol": symbol,
                    "error": str(e)
                }
                return False
            
        except Exception as e:
            print(f"❌ 分析流程测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_configuration_methods(self) -> bool:
        """测试配置方法"""
        try:
            print("🔧 开始测试配置方法...")
            
            if not self.trading_graph:
                print("❌ 交易图未初始化")
                return False
            
            config_methods = [
                "get_current_state",
                "get_analysis_history",
                "backtest"
            ]
            
            config_results = {}
            
            for method_name in config_methods:
                print(f"  🛠️  测试 {method_name}...")
                
                try:
                    if hasattr(self.trading_graph, method_name):
                        method = getattr(self.trading_graph, method_name)
                        if callable(method):
                            print(f"    ✅ 方法可调用")
                            config_results[method_name] = {
                                "status": "success",
                                "callable": True
                            }
                        else:
                            print(f"    ⚠️  方法不可调用")
                            config_results[method_name] = {
                                "status": "success",
                                "callable": False
                            }
                    else:
                        print(f"    ❌ 方法不存在")
                        config_results[method_name] = {
                            "status": "failed",
                            "error": "Method not found"
                        }
                        
                except Exception as e:
                    print(f"    ❌ 测试失败: {str(e)}")
                    config_results[method_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            self.test_results["configuration_methods"] = config_results
            print("✅ 配置方法测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 配置方法测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def run_comprehensive_test(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        """运行综合测试"""
        print("🚀 开始综合系统测试...")
        print("=" * 50)
        
        test_start_time = datetime.now()
        
        # 初始化测试
        tests = [
            ("配置初始化", self.setup_config),
            ("交易图初始化", self.setup_trading_graph),
            ("分析师模块", self.test_analysts),
            ("研究员模块", self.test_researchers),
            ("风险管理模块", self.test_risk_managers),
            ("交易员模块", self.test_trader),
            ("配置方法", self.test_configuration_methods),
            ("分析流程", lambda: self.test_analysis_workflow(symbol))
        ]
        
        test_summary = {}
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}测试")
            print("-" * 30)
            
            try:
                start_time = datetime.now()
                success = test_func()
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                test_summary[test_name] = {
                    "status": "success" if success else "failed",
                    "duration": duration,
                    "timestamp": end_time.isoformat()
                }
                
                if success:
                    print(f"✅ {test_name}测试通过 (耗时: {duration:.2f}秒)")
                else:
                    print(f"❌ {test_name}测试失败 (耗时: {duration:.2f}秒)")
                    
            except Exception as e:
                print(f"❌ {test_name}测试异常: {str(e)}")
                test_summary[test_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        test_end_time = datetime.now()
        total_duration = (test_end_time - test_start_time).total_seconds()
        
        print("\n" + "=" * 50)
        print("📊 测试总结")
        print("=" * 50)
        
        success_count = sum(1 for test in test_summary.values() if test["status"] == "success")
        total_count = len(test_summary)
        
        print(f"总测试数: {total_count}")
        print(f"成功测试: {success_count}")
        print(f"失败测试: {total_count - success_count}")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        print(f"总耗时: {total_duration:.2f}秒")
        
        # 保存测试结果
        results = {
            "test_summary": test_summary,
            "detailed_results": self.test_results,
            "total_duration": total_duration,
            "success_rate": success_count/total_count*100,
            "test_timestamp": test_end_time.isoformat(),
            "symbol": symbol
        }
        
        # 保存到文件
        results_file = f"system_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 详细测试结果已保存到: {results_file}")
        
        return results
    
    def print_test_results(self, results: Dict[str, Any]):
        """打印测试结果"""
        print("\n📋 详细测试结果")
        print("=" * 50)
        
        for test_name, result in results["test_summary"].items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"{status_icon} {test_name}: {result['status']} ({result['duration']:.2f}秒)")
        
        if "detailed_results" in results:
            print("\n🔍 模块详细信息")
            print("-" * 30)
            
            for module_name, module_results in results["detailed_results"].items():
                print(f"\n📦 {module_name}:")
                if isinstance(module_results, dict):
                    for item_name, item_result in module_results.items():
                        if isinstance(item_result, dict):
                            status = item_result.get("status", "unknown")
                            print(f"  {status_icon} {item_name}: {status}")
                        else:
                            print(f"  📄 {item_name}: {item_result}")


def main():
    """主函数"""
    print("🔧 加密货币交易代理系统模块测试器")
    print("=" * 50)
    
    # 创建测试器实例
    tester = SystemModuleTester()
    
    # 运行测试
    try:
        # 可以指定不同的交易对进行测试
        symbol = "BTC/USDT"  # 默认测试BTC/USDT
        
        # 如果有命令行参数，使用第一个参数作为交易对
        if len(sys.argv) > 1:
            symbol = sys.argv[1]
        
        print(f"🎯 测试交易对: {symbol}")
        
        # 运行综合测试
        results = tester.run_comprehensive_test(symbol)
        
        # 打印详细结果
        tester.print_test_results(results)
        
        # 返回退出码
        success_rate = results["success_rate"]
        if success_rate >= 80:
            print(f"\n🎉 测试基本通过 (成功率: {success_rate:.1f}%)")
            sys.exit(0)
        elif success_rate >= 50:
            print(f"\n⚠️  测试部分通过 (成功率: {success_rate:.1f}%)")
            sys.exit(1)
        else:
            print(f"\n❌ 测试失败 (成功率: {success_rate:.1f}%)")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(3)
    except Exception as e:
        print(f"\n\n💥 测试发生异常: {str(e)}")
        traceback.print_exc()
        sys.exit(4)


if __name__ == "__main__":
    main()