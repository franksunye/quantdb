"""
资产信息页面
展示股票的基本信息、财务指标和数据覆盖情况
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from pathlib import Path
import time

# 添加src目录到Python路径
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 页面配置
st.set_page_config(
    page_title="资产信息 - QuantDB",
    page_icon="📊",
    layout="wide"
)

# 初始化服务
@st.cache_resource
def init_services():
    """初始化服务实例"""
    try:
        from services.asset_info_service import AssetInfoService
        from services.stock_data_service import StockDataService
        from cache.akshare_adapter import AKShareAdapter
        from api.database import get_db

        db_session = next(get_db())
        akshare_adapter = AKShareAdapter()
        return {
            'asset_service': AssetInfoService(db_session),
            'stock_service': StockDataService(db_session, akshare_adapter)
        }
    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        return None

def validate_stock_code(code: str) -> bool:
    """验证股票代码格式"""
    if not code:
        return False
    
    code = code.strip()
    
    # 检查是否为6位数字
    if len(code) != 6 or not code.isdigit():
        return False
    
    # 检查是否为有效的A股代码
    if code.startswith(('000', '001', '002', '003', '300')):  # 深交所
        return True
    elif code.startswith('6'):  # 上交所
        return True
    elif code.startswith('688'):  # 科创板
        return True
    
    return False

def format_large_number(num):
    """格式化大数字显示"""
    if pd.isna(num) or num == 0:
        return "N/A"
    
    if num >= 1e8:
        return f"{num/1e8:.2f}亿"
    elif num >= 1e4:
        return f"{num/1e4:.2f}万"
    else:
        return f"{num:.2f}"

def main():
    """主页面"""
    
    st.title("📊 资产信息")
    st.markdown("查看股票的基本信息、财务指标和数据覆盖情况")
    st.markdown("---")
    
    # 初始化服务
    services = init_services()
    if not services:
        st.error("❌ 服务初始化失败，请刷新页面重试")
        return
    
    asset_service = services['asset_service']
    stock_service = services['stock_service']
    
    # 输入区域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        symbol = st.text_input(
            "股票代码",
            placeholder="例如: 600000",
            help="请输入6位A股代码"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 空行对齐
        query_button = st.button("🔍 查询资产信息", type="primary")
    
    # 验证输入并查询
    if query_button:
        if not validate_stock_code(symbol):
            st.error("❌ 请输入有效的6位股票代码（如：600000、000001、300001）")
            return
        
        # 查询资产信息
        with st.spinner("正在获取资产信息..."):
            start_time = time.time()
            
            try:
                # 获取或创建资产信息
                asset_info, metadata = asset_service.get_or_create_asset(symbol)
                response_time = time.time() - start_time
                
                if not asset_info:
                    st.error("❌ 获取资产信息失败，请检查股票代码或稍后重试")
                    return
                
                # 显示成功信息
                st.success(f"✅ 成功获取 {asset_info.name} ({symbol}) 的资产信息 - 响应时间: {response_time:.2f}秒")
                
                # 基本信息卡片
                st.markdown("### 📋 基本信息")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("公司名称", asset_info.name)
                
                with col2:
                    st.metric("股票代码", asset_info.symbol)
                
                with col3:
                    exchange_name = "上交所" if symbol.startswith('6') else "深交所"
                    st.metric("交易所", exchange_name)
                
                with col4:
                    st.metric("行业", asset_info.industry or "N/A")
                
                st.markdown("---")
                
                # 财务指标
                st.markdown("### 💰 财务指标")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    pe_ratio = asset_info.pe_ratio if asset_info.pe_ratio else "N/A"
                    st.metric("市盈率 (PE)", pe_ratio)
                
                with col2:
                    pb_ratio = asset_info.pb_ratio if asset_info.pb_ratio else "N/A"
                    st.metric("市净率 (PB)", pb_ratio)
                
                with col3:
                    roe = asset_info.roe if asset_info.roe else "N/A"
                    st.metric("净资产收益率 (ROE)", f"{roe}%" if roe != "N/A" else "N/A")
                
                with col4:
                    market_cap = format_large_number(asset_info.market_cap)
                    st.metric("总市值", market_cap)
                
                # 第二行财务指标
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_shares = format_large_number(asset_info.total_shares)
                    st.metric("总股本", total_shares)
                
                with col2:
                    circulating_shares = format_large_number(asset_info.circulating_shares)
                    st.metric("流通股本", circulating_shares)
                
                with col3:
                    listing_date = asset_info.listing_date.strftime('%Y-%m-%d') if asset_info.listing_date else "N/A"
                    st.metric("上市日期", listing_date)
                
                with col4:
                    concept = asset_info.concept or "N/A"
                    st.metric("概念分类", concept)
                
                st.markdown("---")
                
                # 数据覆盖情况
                st.markdown("### 📈 数据覆盖情况")
                
                try:
                    # 获取历史数据统计
                    from api.models import DailyStockData
                    from api.database import get_db

                    db_session = next(get_db())
                    data_records = db_session.query(DailyStockData).filter(
                        DailyStockData.symbol == symbol
                    ).all()

                    if data_records:
                        col1, col2, col3, col4 = st.columns(4)

                        dates = [record.trade_date for record in data_records]
                        start_date = min(dates)
                        end_date = max(dates)
                        data_span = (end_date - start_date).days

                        with col1:
                            st.metric("数据记录数", f"{len(data_records):,}条")

                        with col2:
                            st.metric("数据起始", start_date.strftime('%Y-%m-%d'))

                        with col3:
                            st.metric("数据截止", end_date.strftime('%Y-%m-%d'))

                        with col4:
                            st.metric("数据跨度", f"{data_span}天")
                    else:
                        st.info("📝 暂无历史数据，请先在股票数据查询页面获取数据")

                except Exception as e:
                    st.warning(f"⚠️ 获取数据覆盖信息失败: {str(e)}")
                
                # 元数据信息
                with st.expander("📊 元数据信息"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**数据来源**:", asset_info.data_source or "AKShare")
                        st.write("**最后更新**:", asset_info.last_updated.strftime('%Y-%m-%d %H:%M:%S') if asset_info.last_updated else "N/A")
                        st.write("**资产类型**:", asset_info.asset_type)
                    
                    with col2:
                        st.write("**货币单位**:", asset_info.currency)
                        st.write("**ISIN代码**:", asset_info.isin)
                        st.write("**响应时间**:", f"{response_time:.3f}秒")
                
                # 刷新按钮
                st.markdown("---")
                if st.button("🔄 刷新资产信息"):
                    with st.spinner("正在刷新资产信息..."):
                        try:
                            # 强制刷新资产信息
                            updated_asset = asset_service.update_asset_info(symbol)
                            if updated_asset:
                                st.success("✅ 资产信息已刷新")
                                st.experimental_rerun()
                            else:
                                st.error("❌ 刷新失败")
                        except Exception as e:
                            st.error(f"❌ 刷新过程中出现错误: {str(e)}")
                
            except Exception as e:
                st.error(f"❌ 查询过程中出现错误: {str(e)}")
                st.info("请检查网络连接或稍后重试")

if __name__ == "__main__":
    main()
