#!/usr/bin/env python3
"""
股票代码验证和推荐工具
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 已知的活跃股票列表
ACTIVE_STOCKS = {
    # 银行股
    '600000': '浦发银行',
    '000001': '平安银行', 
    '600036': '招商银行',
    '601166': '兴业银行',
    '000002': '万科A',
    
    # 白酒股
    '600519': '贵州茅台',
    '000858': '五粮液',
    '000568': '泸州老窖',
    
    # 科技股
    '000002': '万科A',
    '002415': '海康威视',
    '000725': '京东方A',
    
    # 其他蓝筹股
    '600519': '贵州茅台',
    '000858': '五粮液',
    '600036': '招商银行'
}

# 已知的问题股票（停牌、退市等）
PROBLEMATIC_STOCKS = {
    '600001': '邯郸钢铁 - 可能已停牌或退市',
    '600002': '齐鲁石化 - 可能已停牌或退市', 
    '600003': '东北高速 - 可能已停牌或退市',
    '600004': '白云机场 - 数据可能不完整',
    '600005': '武钢股份 - 已重组',
}

def validate_stock_code(symbol: str) -> Dict[str, any]:
    """
    验证股票代码的有效性
    
    Args:
        symbol: 股票代码
        
    Returns:
        验证结果字典
    """
    result = {
        "is_valid": False,
        "is_active": False,
        "is_problematic": False,
        "exchange": None,
        "name": None,
        "status": "unknown",
        "recommendations": []
    }
    
    # 基本格式验证
    if not symbol or len(symbol) != 6 or not symbol.isdigit():
        result["status"] = "invalid_format"
        result["recommendations"].append("股票代码应为6位数字")
        return result
    
    result["is_valid"] = True
    
    # 判断交易所
    if symbol.startswith('6'):
        result["exchange"] = "上海证券交易所"
    elif symbol.startswith('0') or symbol.startswith('3'):
        result["exchange"] = "深圳证券交易所"
    elif symbol.startswith('8') or symbol.startswith('4'):
        result["exchange"] = "北京证券交易所"
    else:
        result["exchange"] = "未知交易所"
    
    # 检查是否为活跃股票
    if symbol in ACTIVE_STOCKS:
        result["is_active"] = True
        result["name"] = ACTIVE_STOCKS[symbol]
        result["status"] = "active"
    
    # 检查是否为问题股票
    if symbol in PROBLEMATIC_STOCKS:
        result["is_problematic"] = True
        result["name"] = PROBLEMATIC_STOCKS[symbol]
        result["status"] = "problematic"
        result["recommendations"].append("建议选择其他活跃股票")
    
    return result

def get_stock_recommendations(exclude_symbol: str = None) -> List[Dict[str, str]]:
    """
    获取推荐的股票列表
    
    Args:
        exclude_symbol: 要排除的股票代码
        
    Returns:
        推荐股票列表
    """
    recommendations = []
    
    for symbol, name in ACTIVE_STOCKS.items():
        if symbol != exclude_symbol:
            recommendations.append({
                "symbol": symbol,
                "name": name,
                "reason": "活跃交易股票"
            })
    
    # 按类别排序
    priority_stocks = ['600000', '000001', '600519', '600036']
    
    # 优先推荐
    priority_recommendations = [r for r in recommendations if r["symbol"] in priority_stocks]
    other_recommendations = [r for r in recommendations if r["symbol"] not in priority_stocks]
    
    return priority_recommendations[:3] + other_recommendations[:2]

def analyze_query_failure(symbol: str, start_date: str, end_date: str) -> Dict[str, any]:
    """
    分析查询失败的原因
    
    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        
    Returns:
        分析结果
    """
    analysis = {
        "stock_validation": validate_stock_code(symbol),
        "date_analysis": {},
        "possible_reasons": [],
        "recommendations": [],
        "suggested_stocks": []
    }
    
    # 日期分析
    try:
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        date_diff = (end_dt - start_dt).days
        
        analysis["date_analysis"] = {
            "days_requested": date_diff,
            "start_date": start_date,
            "end_date": end_date,
            "is_weekend_only": _is_weekend_only(start_dt, end_dt),
            "is_too_short": date_diff < 7
        }
        
        # 分析可能的原因
        if analysis["date_analysis"]["is_weekend_only"]:
            analysis["possible_reasons"].append("选择的日期范围可能只包含周末")
            analysis["recommendations"].append("选择包含工作日的日期范围")
        
        if analysis["date_analysis"]["is_too_short"]:
            analysis["possible_reasons"].append("查询时间范围太短")
            analysis["recommendations"].append("建议查询至少30天的数据")
            
    except ValueError:
        analysis["possible_reasons"].append("日期格式错误")
        analysis["recommendations"].append("检查日期格式是否正确")
    
    # 股票相关分析
    stock_validation = analysis["stock_validation"]
    
    if stock_validation["is_problematic"]:
        analysis["possible_reasons"].append(f"股票可能有问题: {stock_validation['name']}")
        analysis["recommendations"].append("尝试查询其他活跃股票")
    
    if not stock_validation["is_active"]:
        analysis["possible_reasons"].append("股票可能不够活跃或已停牌")
        analysis["recommendations"].append("选择知名的活跃股票")
    
    # 获取推荐股票
    analysis["suggested_stocks"] = get_stock_recommendations(exclude_symbol=symbol)
    
    return analysis

def _is_weekend_only(start_dt: datetime, end_dt: datetime) -> bool:
    """
    检查日期范围是否只包含周末
    
    Args:
        start_dt: 开始日期
        end_dt: 结束日期
        
    Returns:
        是否只包含周末
    """
    current_dt = start_dt
    has_weekday = False
    
    while current_dt <= end_dt:
        if current_dt.weekday() < 5:  # 0-4 是周一到周五
            has_weekday = True
            break
        current_dt += timedelta(days=1)
    
    return not has_weekday

def get_alternative_suggestions(symbol: str) -> List[Dict[str, str]]:
    """
    为问题股票提供替代建议
    
    Args:
        symbol: 原始股票代码
        
    Returns:
        替代建议列表
    """
    suggestions = []
    
    # 基于股票代码前缀提供同类型建议
    if symbol.startswith('6'):  # 上海股票
        suggestions.extend([
            {"symbol": "600000", "name": "浦发银行", "reason": "同为上海交易所银行股"},
            {"symbol": "600036", "name": "招商银行", "reason": "同为上海交易所银行股"},
            {"symbol": "600519", "name": "贵州茅台", "reason": "上海交易所蓝筹股"}
        ])
    elif symbol.startswith('0'):  # 深圳主板
        suggestions.extend([
            {"symbol": "000001", "name": "平安银行", "reason": "同为深圳交易所银行股"},
            {"symbol": "000002", "name": "万科A", "reason": "深圳交易所蓝筹股"},
            {"symbol": "000858", "name": "五粮液", "reason": "深圳交易所白酒股"}
        ])
    
    return suggestions[:3]

# 使用示例
if __name__ == "__main__":
    # 测试股票验证
    test_symbols = ['600001', '600000', '000001', '123456', 'INVALID']
    
    for symbol in test_symbols:
        result = validate_stock_code(symbol)
        print(f"股票 {symbol}: {result}")
    
    # 测试查询失败分析
    analysis = analyze_query_failure('600001', '20241214', '20241220')
    print(f"\n查询失败分析: {analysis}")
