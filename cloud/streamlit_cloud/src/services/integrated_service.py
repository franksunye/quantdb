"""
集成服务层 - 适配Streamlit Cloud的单体架构
整合AKShare数据获取、缓存管理和性能监控
"""

import streamlit as st
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import time
from typing import Dict, Any, Optional, List

class IntegratedQuantDBService:
    """集成的QuantDB服务"""

    def __init__(self):
        self._init_session_state()

    def _init_session_state(self):
        """初始化会话状态"""
        defaults = {
            'stock_data_cache': {},
            'asset_info_cache': {},
            'performance_metrics': {
                'total_queries': 0,
                'cache_hits': 0,
                'akshare_calls': 0,
                'avg_response_time': 0,
                'query_history': []
            },
            'user_preferences': {
                'default_days': 30,
                'chart_theme': 'plotly_white',
                'auto_refresh': False
            },
            'app_start_time': datetime.now(),
            'last_activity': datetime.now()
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def get_stock_data(self, symbol: str, start_date: str, end_date: str, adjust: str = "") -> Optional[Dict[str, Any]]:
        """获取股票历史数据"""
        cache_key = f"{symbol}_{start_date}_{end_date}_{adjust}"

        # 检查缓存
        if cache_key in st.session_state.stock_data_cache:
            self._update_performance_metrics('stock_data', 0.01, cache_hit=True)
            cached_result = st.session_state.stock_data_cache[cache_key]
            return {
                'data': cached_result['data'],
                'metadata': {
                    **cached_result['metadata'],
                    'cache_hit': True,
                    'response_time_ms': 10
                }
            }

        # 从AKShare获取数据
        try:
            start_time = time.time()

            # 格式化日期
            start_date_formatted = start_date.replace('-', '')
            end_date_formatted = end_date.replace('-', '')

            # 获取股票历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date_formatted,
                end_date=end_date_formatted,
                adjust=adjust
            )

            if df.empty:
                return None

            # 数据处理
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'turnover', 'amplitude', 'pct_change', 'change', 'turnover_rate']
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # 获取股票基本信息
            stock_info = self._get_stock_basic_info(symbol)

            response_time = time.time() - start_time

            result = {
                'data': df.to_dict('records'),
                'metadata': {
                    'symbol': symbol,
                    'name': stock_info.get('name', f'股票{symbol}'),
                    'total_records': len(df),
                    'data_source': 'AKShare',
                    'fetch_time': datetime.now().isoformat(),
                    'response_time_ms': response_time * 1000,
                    'cache_hit': False,
                    'akshare_called': True
                }
            }

            # 缓存结果
            st.session_state.stock_data_cache[cache_key] = result
            self._update_performance_metrics('stock_data', response_time, cache_hit=False)

            return result

        except Exception as e:
            st.error(f"获取股票数据失败: {str(e)}")
            return None

    def get_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取资产信息"""
        # 检查缓存
        if symbol in st.session_state.asset_info_cache:
            self._update_performance_metrics('asset_info', 0.01, cache_hit=True)
            return st.session_state.asset_info_cache[symbol]

        try:
            start_time = time.time()

            # 获取股票基本信息
            basic_info = self._get_stock_basic_info(symbol)

            # 获取实时数据
            realtime_data = self._get_realtime_data(symbol)

            response_time = time.time() - start_time

            result = {
                'symbol': symbol,
                'name': basic_info.get('name', f'股票{symbol}'),
                'basic_info': basic_info,
                'realtime_data': realtime_data,
                'metadata': {
                    'data_source': 'AKShare',
                    'fetch_time': datetime.now().isoformat(),
                    'response_time': response_time
                }
            }

            # 缓存结果
            st.session_state.asset_info_cache[symbol] = result
            self._update_performance_metrics('asset_info', response_time, cache_hit=False)

            return result

        except Exception as e:
            st.error(f"获取资产信息失败: {str(e)}")
            return None

    def get_assets_list(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取资产列表（模拟数据）"""
        # 返回一些常用的股票代码作为示例
        sample_stocks = [
            {'symbol': '600000', 'name': '浦发银行', 'industry': '银行'},
            {'symbol': '000001', 'name': '平安银行', 'industry': '银行'},
            {'symbol': '600519', 'name': '贵州茅台', 'industry': '食品饮料'},
            {'symbol': '000002', 'name': '万科A', 'industry': '房地产'},
            {'symbol': '600036', 'name': '招商银行', 'industry': '银行'},
            {'symbol': '000858', 'name': '五粮液', 'industry': '食品饮料'},
            {'symbol': '600276', 'name': '恒瑞医药', 'industry': '医药生物'},
            {'symbol': '000166', 'name': '申万宏源', 'industry': '非银金融'},
            {'symbol': '600887', 'name': '伊利股份', 'industry': '食品饮料'},
            {'symbol': '000063', 'name': '中兴通讯', 'industry': '通信'}
        ]
        
        return sample_stocks[:limit]

    def _get_stock_basic_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            # 获取股票基本信息
            info_df = ak.stock_individual_info_em(symbol=symbol)
            if not info_df.empty:
                info_dict = dict(zip(info_df['item'], info_df['value']))
                return {
                    'name': info_dict.get('股票简称', f'股票{symbol}'),
                    'industry': info_dict.get('所属行业', '未知'),
                    'exchange': '上交所' if symbol.startswith('6') else '深交所',
                    'listing_date': info_dict.get('上市时间', '未知'),
                    'total_shares': info_dict.get('总股本', 0),
                    'circulating_shares': info_dict.get('流通股', 0)
                }
        except:
            pass

        return {
            'name': f'股票{symbol}',
            'industry': '未知',
            'exchange': '上交所' if symbol.startswith('6') else '深交所',
            'listing_date': '未知',
            'total_shares': 0,
            'circulating_shares': 0
        }

    def _get_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """获取实时数据"""
        try:
            # 获取实时数据
            realtime_df = ak.stock_zh_a_spot_em()
            stock_data = realtime_df[realtime_df['代码'] == symbol]

            if not stock_data.empty:
                row = stock_data.iloc[0]
                return {
                    'current_price': row.get('最新价', 0),
                    'change': row.get('涨跌额', 0),
                    'pct_change': row.get('涨跌幅', 0),
                    'volume': row.get('成交量', 0),
                    'turnover': row.get('成交额', 0),
                    'pe_ratio': row.get('市盈率-动态', 0),
                    'pb_ratio': row.get('市净率', 0),
                    'market_cap': row.get('总市值', 0)
                }
        except:
            pass

        return {
            'current_price': 0,
            'change': 0,
            'pct_change': 0,
            'volume': 0,
            'turnover': 0,
            'pe_ratio': 0,
            'pb_ratio': 0,
            'market_cap': 0
        }

    def _update_performance_metrics(self, query_type: str, response_time: float, cache_hit: bool = False):
        """更新性能指标"""
        metrics = st.session_state.performance_metrics
        
        metrics['total_queries'] += 1
        if cache_hit:
            metrics['cache_hits'] += 1
        else:
            metrics['akshare_calls'] += 1
        
        # 更新平均响应时间
        current_avg = metrics['avg_response_time']
        total_queries = metrics['total_queries']
        metrics['avg_response_time'] = (current_avg * (total_queries - 1) + response_time) / total_queries
        
        # 记录查询历史（保持最近50条）
        metrics['query_history'].append({
            'timestamp': datetime.now(),
            'query_type': query_type,
            'response_time': response_time,
            'cache_hit': cache_hit
        })
        
        if len(metrics['query_history']) > 50:
            metrics['query_history'] = metrics['query_history'][-50:]

    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        metrics = st.session_state.performance_metrics
        
        return {
            'stock_data_count': len(st.session_state.stock_data_cache),
            'asset_info_count': len(st.session_state.asset_info_cache),
            'total_queries': metrics['total_queries'],
            'cache_hits': metrics['cache_hits'],
            'akshare_calls': metrics['akshare_calls'],
            'cache_hit_rate': (
                metrics['cache_hits'] / max(metrics['total_queries'], 1) * 100
            ),
            'avg_response_time': metrics['avg_response_time'],
            'session_duration': datetime.now() - st.session_state.app_start_time,
            'last_activity': st.session_state.last_activity
        }

    def clear_cache(self):
        """清空缓存"""
        st.session_state.stock_data_cache = {}
        st.session_state.asset_info_cache = {}
        st.session_state.performance_metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'akshare_calls': 0,
            'avg_response_time': 0,
            'query_history': []
        }
        st.success("缓存已清空")
