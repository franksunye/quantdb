#!/usr/bin/env python3
"""
股票代码验证和推荐工具
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 已知的活跃股票列表 - 支持A股和港股
ACTIVE_STOCKS = {
    # A股银行股
    "600000": "浦发银行",
    "000001": "平安银行",
    "600036": "招商银行",
    "601166": "兴业银行",
    "000002": "万科A",
    # A股白酒股
    "600519": "贵州茅台",
    "000858": "五粮液",
    "000568": "泸州老窖",
    # A股科技股
    "002415": "海康威视",
    "000725": "京东方A",
    # 港股 - 知名股票
    "00700": "腾讯控股",
    "09988": "阿里巴巴-SW",
    "03690": "美团-W",
    "01810": "小米集团-W",
    "02318": "中国平安",
    "00941": "中国移动",
    "01398": "工商银行",
    "00939": "建设银行",
    "02171": "招商局港口",
    "01299": "友邦保险",
}

# 已知的问题股票（停牌、退市等）
PROBLEMATIC_STOCKS = {
    "600001": "邯郸钢铁 - 可能已停牌或退市",
    "600002": "齐鲁石化 - 可能已停牌或退市",
    "600003": "东北高速 - 可能已停牌或退市",
    "600004": "白云机场 - 数据可能不完整",
    "600005": "武钢股份 - 已重组",
}


def validate_stock_code(symbol: str) -> Dict[str, any]:
    """
    验证股票代码的有效性 - 支持A股和港股

    Args:
        symbol: 股票代码 (A股: 600000, 港股: 00700)

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
        "market": None,
        "recommendations": [],
    }

    if not symbol:
        result["status"] = "invalid_format"
        result["recommendations"].append("请输入股票代码")
        return result

    # 检测是否为港股 (5位数字)
    if symbol.isdigit() and len(symbol) == 5:
        result["is_valid"] = True
        result["market"] = "港股"
        result["exchange"] = "香港交易所"

        # 检查是否为活跃港股
        if symbol in ACTIVE_STOCKS:
            result["is_active"] = True
            result["name"] = ACTIVE_STOCKS[symbol]
            result["status"] = "active"
        else:
            result["status"] = "unknown_hk_stock"
            result["recommendations"].append(
                "建议选择知名港股如腾讯(00700)、阿里巴巴(09988)"
            )

        return result

    # A股验证 (6位数字)
    if not symbol.isdigit() or len(symbol) != 6:
        result["status"] = "invalid_format"
        result["recommendations"].append("股票代码应为6位数字(A股)或5位数字(港股)")
        return result

    result["is_valid"] = True
    result["market"] = "A股"

    # 判断A股交易所
    if symbol.startswith("6"):
        result["exchange"] = "上海证券交易所"
    elif symbol.startswith("0") or symbol.startswith("3"):
        result["exchange"] = "深圳证券交易所"
    elif symbol.startswith("8") or symbol.startswith("4"):
        result["exchange"] = "北京证券交易所"
    else:
        result["exchange"] = "未知交易所"

    # 检查是否为活跃A股
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


def get_stock_recommendations(
    exclude_symbol: str = None, market: str = "all"
) -> List[Dict[str, str]]:
    """
    获取推荐的股票列表 - 支持A股和港股

    Args:
        exclude_symbol: 要排除的股票代码
        market: 市场类型 ("all", "A股", "港股")

    Returns:
        推荐股票列表
    """
    recommendations = []

    for symbol, name in ACTIVE_STOCKS.items():
        if symbol != exclude_symbol:
            # 判断股票市场
            stock_market = "港股" if len(symbol) == 5 else "A股"

            # 根据市场筛选
            if market == "all" or market == stock_market:
                recommendations.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "market": stock_market,
                        "reason": f"活跃{stock_market}股票",
                    }
                )

    # 按类别排序 - A股和港股分别优先推荐
    a_stock_priority = ["600000", "000001", "600519", "600036"]  # A股优先
    hk_stock_priority = ["00700", "09988", "03690", "01810"]  # 港股优先

    # 分类推荐
    a_stock_recommendations = [r for r in recommendations if r["market"] == "A股"]
    hk_stock_recommendations = [r for r in recommendations if r["market"] == "港股"]

    # A股优先推荐
    a_priority = [r for r in a_stock_recommendations if r["symbol"] in a_stock_priority]
    a_others = [
        r for r in a_stock_recommendations if r["symbol"] not in a_stock_priority
    ]

    # 港股优先推荐
    hk_priority = [
        r for r in hk_stock_recommendations if r["symbol"] in hk_stock_priority
    ]
    hk_others = [
        r for r in hk_stock_recommendations if r["symbol"] not in hk_stock_priority
    ]

    # 根据市场返回推荐
    if market == "A股":
        return a_priority[:3] + a_others[:2]
    elif market == "港股":
        return hk_priority[:3] + hk_others[:2]
    else:
        # 混合推荐：A股和港股各推荐几只
        return a_priority[:2] + hk_priority[:2] + a_others[:1]


def analyze_query_failure(
    symbol: str, start_date: str, end_date: str
) -> Dict[str, any]:
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
        "suggested_stocks": [],
    }

    # 日期分析
    try:
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")
        date_diff = (end_dt - start_dt).days

        analysis["date_analysis"] = {
            "days_requested": date_diff,
            "start_date": start_date,
            "end_date": end_date,
            "is_weekend_only": _is_weekend_only(start_dt, end_dt),
            "is_too_short": date_diff < 7,
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
        analysis["possible_reasons"].append(
            f"股票可能有问题: {stock_validation['name']}"
        )
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
    为问题股票提供替代建议 - 支持A股和港股

    Args:
        symbol: 原始股票代码

    Returns:
        替代建议列表
    """
    suggestions = []

    # 检测是否为港股
    if symbol.isdigit() and len(symbol) == 5:
        # 港股替代建议
        suggestions.extend(
            [
                {
                    "symbol": "00700",
                    "name": "腾讯控股",
                    "reason": "港股科技龙头",
                    "market": "港股",
                },
                {
                    "symbol": "09988",
                    "name": "阿里巴巴-SW",
                    "reason": "港股互联网巨头",
                    "market": "港股",
                },
                {
                    "symbol": "03690",
                    "name": "美团-W",
                    "reason": "港股生活服务平台",
                    "market": "港股",
                },
                {
                    "symbol": "01810",
                    "name": "小米集团-W",
                    "reason": "港股智能手机厂商",
                    "market": "港股",
                },
            ]
        )
    else:
        # A股替代建议 - 基于股票代码前缀提供同类型建议
        if symbol.startswith("6"):  # 上海股票
            suggestions.extend(
                [
                    {
                        "symbol": "600000",
                        "name": "浦发银行",
                        "reason": "同为上海交易所银行股",
                        "market": "A股",
                    },
                    {
                        "symbol": "600036",
                        "name": "招商银行",
                        "reason": "同为上海交易所银行股",
                        "market": "A股",
                    },
                    {
                        "symbol": "600519",
                        "name": "贵州茅台",
                        "reason": "上海交易所蓝筹股",
                        "market": "A股",
                    },
                ]
            )
        elif symbol.startswith("0"):  # 深圳主板
            suggestions.extend(
                [
                    {
                        "symbol": "000001",
                        "name": "平安银行",
                        "reason": "同为深圳交易所银行股",
                        "market": "A股",
                    },
                    {
                        "symbol": "000002",
                        "name": "万科A",
                        "reason": "深圳交易所蓝筹股",
                        "market": "A股",
                    },
                    {
                        "symbol": "000858",
                        "name": "五粮液",
                        "reason": "深圳交易所白酒股",
                        "market": "A股",
                    },
                ]
            )
        else:
            # 通用A股推荐
            suggestions.extend(
                [
                    {
                        "symbol": "600000",
                        "name": "浦发银行",
                        "reason": "A股银行龙头",
                        "market": "A股",
                    },
                    {
                        "symbol": "600519",
                        "name": "贵州茅台",
                        "reason": "A股白酒龙头",
                        "market": "A股",
                    },
                    {
                        "symbol": "000001",
                        "name": "平安银行",
                        "reason": "A股股份制银行",
                        "market": "A股",
                    },
                ]
            )

    return suggestions[:3]


# 使用示例
if __name__ == "__main__":
    # 测试股票验证 - A股和港股
    test_symbols = ["600001", "600000", "000001", "00700", "09988", "123456", "INVALID"]

    print("=== 股票代码验证测试 ===")
    for symbol in test_symbols:
        result = validate_stock_code(symbol)
        print(
            f"股票 {symbol}: 市场={result.get('market', 'N/A')}, 有效={result['is_valid']}, 活跃={result['is_active']}, 名称={result.get('name', 'N/A')}"
        )

    # 测试推荐功能
    print("\n=== 推荐股票测试 ===")
    print("全市场推荐:", get_stock_recommendations(market="all"))
    print("A股推荐:", get_stock_recommendations(market="A股"))
    print("港股推荐:", get_stock_recommendations(market="港股"))

    # 测试替代建议
    print("\n=== 替代建议测试 ===")
    print("A股替代建议:", get_alternative_suggestions("600001"))
    print("港股替代建议:", get_alternative_suggestions("00001"))

    # 测试查询失败分析
    print("\n=== 查询失败分析测试 ===")
    analysis = analyze_query_failure("600001", "20241214", "20241220")
    print(f"A股分析: {analysis['stock_validation']['market']}")

    hk_analysis = analyze_query_failure("00700", "20241214", "20241220")
    print(f"港股分析: {hk_analysis['stock_validation']['market']}")
