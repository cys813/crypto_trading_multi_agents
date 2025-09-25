"""
交易所数据源设置工具

用于初始化和配置交易所数据源
"""

import os
import sys
from typing import Dict, Any, Optional

# 添加数据源路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data_sources'))

from exchange_data_sources import (
    BinanceDataSource, 
    CoinbaseDataSource, 
    OKXDataSource, 
    HuobiDataSource,
    exchange_manager
)


class ExchangeSetup:
    """交易所设置管理器"""
    
    def __init__(self):
        """初始化交易所设置"""
        self.exchange_configs = {
            'binance': {
                'api_key': os.getenv('BINANCE_API_KEY'),
                'api_secret': os.getenv('BINANCE_API_SECRET'),
                'testnet': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
            },
            'coinbase': {
                'api_key': os.getenv('COINBASE_API_KEY'),
                'api_secret': os.getenv('COINBASE_API_SECRET'),
                'passphrase': os.getenv('COINBASE_PASSPHRASE')
            },
            'okx': {
                'api_key': os.getenv('OKX_API_KEY'),
                'api_secret': os.getenv('OKX_API_SECRET'),
                'passphrase': os.getenv('OKX_PASSPHRASE')
            },
            'huobi': {
                'api_key': os.getenv('HUOBI_API_KEY'),
                'api_secret': os.getenv('HUOBI_API_SECRET')
            }
        }
    
    def setup_exchanges(self) -> Dict[str, Any]:
        """
        设置所有交易所
        
        Returns:
            设置结果
        """
        results = {
            'success': [],
            'failed': [],
            'total': 0
        }
        
        # 设置Binance
        try:
            binance_config = self.exchange_configs['binance']
            if binance_config['api_key'] and binance_config['api_secret']:
                binance = BinanceDataSource(
                    api_key=binance_config['api_key'],
                    api_secret=binance_config['api_secret'],
                    testnet=binance_config['testnet']
                )
                exchange_manager.register_exchange('binance', binance)
                results['success'].append('binance')
                print("✓ Binance交易所设置成功")
            else:
                # 设置无API密钥的Binance（只读）
                binance = BinanceDataSource()
                exchange_manager.register_exchange('binance', binance)
                results['success'].append('binance_readonly')
                print("✓ Binance交易所设置成功（只读模式）")
        except Exception as e:
            results['failed'].append({'exchange': 'binance', 'error': str(e)})
            print(f"✗ Binance交易所设置失败: {e}")
        
        # 设置OKX
        try:
            okx_config = self.exchange_configs['okx']
            if okx_config['api_key'] and okx_config['api_secret']:
                okx = OKXDataSource(
                    api_key=okx_config['api_key'],
                    api_secret=okx_config['api_secret'],
                    passphrase=okx_config['passphrase']
                )
                exchange_manager.register_exchange('okx', okx)
                results['success'].append('okx')
                print("✓ OKX交易所设置成功")
        except Exception as e:
            results['failed'].append({'exchange': 'okx', 'error': str(e)})
            print(f"✗ OKX交易所设置失败: {e}")
        
        # 设置Huobi
        try:
            huobi_config = self.exchange_configs['huobi']
            if huobi_config['api_key'] and huobi_config['api_secret']:
                huobi = HuobiDataSource(
                    api_key=huobi_config['api_key'],
                    api_secret=huobi_config['api_secret']
                )
                exchange_manager.register_exchange('huobi', huobi)
                results['success'].append('huobi')
                print("✓ Huobi交易所设置成功")
        except Exception as e:
            results['failed'].append({'exchange': 'huobi', 'error': str(e)})
            print(f"✗ Huobi交易所设置失败: {e}")
        
        # 设置Coinbase
        try:
            coinbase_config = self.exchange_configs['coinbase']
            if (coinbase_config['api_key'] and coinbase_config['api_secret'] and 
                coinbase_config['passphrase']):
                coinbase = CoinbaseDataSource(
                    api_key=coinbase_config['api_key'],
                    api_secret=coinbase_config['api_secret'],
                    passphrase=coinbase_config['passphrase']
                )
                exchange_manager.register_exchange('coinbase', coinbase)
                results['success'].append('coinbase')
                print("✓ Coinbase交易所设置成功")
        except Exception as e:
            results['failed'].append({'exchange': 'coinbase', 'error': str(e)})
            print(f"✗ Coinbase交易所设置失败: {e}")
        
        results['total'] = len(results['success']) + len(results['failed'])
        
        return results
    
    def test_exchange_connection(self, exchange_name: str = 'binance', symbol: str = 'BTC/USDT') -> bool:
        """
        测试交易所连接
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            
        Returns:
            连接是否成功
        """
        try:
            exchange = exchange_manager.get_exchange(exchange_name)
            if not exchange:
                print(f"交易所 {exchange_name} 未设置")
                return False
            
            # 测试获取行情数据
            ticker = exchange.get_ticker(symbol)
            if ticker:
                print(f"✓ {exchange_name} 连接成功")
                print(f"  当前价格: {ticker['price']}")
                print(f"  24小时成交量: {ticker['volume']}")
                return True
            else:
                print(f"✗ {exchange_name} 无法获取数据")
                return False
                
        except Exception as e:
            print(f"✗ {exchange_name} 连接测试失败: {e}")
            return False
    
    def get_exchange_status(self) -> Dict[str, Any]:
        """
        获取交易所状态
        
        Returns:
            交易所状态信息
        """
        status = {}
        
        for exchange_name in exchange_manager.exchanges.keys():
            try:
                exchange = exchange_manager.get_exchange(exchange_name)
                if exchange and exchange.exchange:
                    status[exchange_name] = {
                        'status': 'active',
                        'has_api_keys': bool(exchange.api_key),
                        'exchange_name': exchange.exchange.name,
                        'sandbox': getattr(exchange.exchange, 'sandbox', False)
                    }
                else:
                    status[exchange_name] = {
                        'status': 'inactive',
                        'has_api_keys': False,
                        'exchange_name': None,
                        'sandbox': False
                    }
            except Exception as e:
                status[exchange_name] = {
                    'status': 'error',
                    'error': str(e),
                    'has_api_keys': False,
                    'exchange_name': None,
                    'sandbox': False
                }
        
        return status
    
    def print_setup_guide(self):
        """打印设置指南"""
        print("""
交易所API密钥设置指南
====================

1. Binance (推荐用于测试)
   - 访问 https://binance.com
   - 创建API密钥
   - 设置环境变量:
     export BINANCE_API_KEY="your_api_key"
     export BINANCE_API_SECRET="your_api_secret"
     export BINANCE_TESTNET="true"  # 可选，用于测试网

2. OKX
   - 访问 https://okx.com
   - 创建API密钥
   - 设置环境变量:
     export OKX_API_KEY="your_api_key"
     export OKX_API_SECRET="your_api_secret"
     export OKX_PASSPHRASE="your_passphrase"

3. Huobi
   - 访问 https://huobi.com
   - 创建API密钥
   - 设置环境变量:
     export HUOBI_API_KEY="your_api_key"
     export HUOBI_API_SECRET="your_api_secret"

4. Coinbase
   - 访问 https://pro.coinbase.com
   - 创建API密钥
   - 设置环境变量:
     export COINBASE_API_KEY="your_api_key"
     export COINBASE_API_SECRET="your_api_secret"
     export COINBASE_PASSPHRASE="your_passphrase"

注意:
- 无需API密钥也可使用Binance的只读模式
- 建议先在测试网环境中测试
- 请妥善保管API密钥，不要提交到代码仓库
""")


# 全局交易所设置实例
exchange_setup = ExchangeSetup()


def initialize_exchanges():
    """初始化交易所设置"""
    print("正在初始化交易所数据源...")
    
    # 设置交易所
    results = exchange_setup.setup_exchanges()
    
    print(f"\n设置结果: {len(results['success'])} 成功, {len(results['failed'])} 失败")
    
    # 测试连接
    if results['success']:
        print("\n测试交易所连接...")
        for exchange_name in results['success']:
            if exchange_name != 'binance_readonly':
                exchange_setup.test_exchange_connection(exchange_name.split('_')[0])
    
    # 显示状态
    print("\n交易所状态:")
    status = exchange_setup.get_exchange_status()
    for name, info in status.items():
        status_icon = "✓" if info['status'] == 'active' else "✗"
        print(f"  {status_icon} {name}: {info['status']}")
        if info['exchange_name']:
            print(f"    交易所: {info['exchange_name']}")
        if info['sandbox']:
            print(f"    模式: 测试网")
    
    return results


if __name__ == "__main__":
    # 初始化交易所
    initialize_exchanges()