import streamlit as st
import requests
import time
from datetime import datetime

# ===== 配置区 =====
API_URL = st.secrets.get("API_URL", "https://api.coingecko.com/api/v3/coins/bitcoin")
CURRENCY = "usd"
REFRESH_INTERVAL = 300  # 5分钟自动刷新
RATE_LIMIT = 10  # 10秒请求间隔

# ===== 样式配置 =====
PRICE_STYLE = """
<style>
.price-display {
    text-align: center; 
    margin-bottom: 30px;
}
.price-value {
    font-size: 3.5rem; 
    color: #f7931a;
}
.change-positive {
    color: #16c784;
}
.change-negative {
    color: #ea3943;
}
</style>
"""

# ===== 初始化状态 =====
state_defaults = {
    'last_updated': "Never",
    'price_data': None,
    'error': None,
    'last_request': 0
}
for key, val in state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ===== 核心函数 =====
def fetch_bitcoin_data():
    """从API获取比特币数据"""
    current_time = time.time()
    
    # 请求频率限制
    if current_time - st.session_state.last_request < RATE_LIMIT:
        st.session_state.error = f"请等待{RATE_LIMIT}秒后再刷新"
        return
    
    st.session_state.last_request = current_time
    
    try:
        # 添加请求重试机制
        for attempt in range(3):
            try:
                response = requests.get(
                    API_URL,
                    headers={"Accept": "application/json"},
                    timeout=5
                )
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                if attempt == 2:
                    raise
                time.sleep(1)
        
        data = response.json()
        
        # 数据验证
        required_fields = [
            "market_data.current_price.usd",
            "market_data.price_change_24h_in_currency.usd",
            "market_data.price_change_percentage_24h_in_currency.usd",
            "market_data.last_updated"
        ]
        
        if not all(field in data for field in required_fields):
            raise ValueError("API返回数据不完整")
        
        price_data = {
            "current_price": float(data["market_data"]["current_price"][CURRENCY]),
            "price_change_24h": float(data["market_data"]["price_change_24h_in_currency"][CURRENCY]),
            "price_change_percentage_24h": float(data["market_data"]["price_change_percentage_24h_in_currency"][CURRENCY]),
            "last_updated": datetime.fromtimestamp(data["market_data"]["last_updated"]).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        st.session_state.price_data = price_data
        st.session_state.last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.session_state.error = None
        
    except requests.exceptions.Timeout:
        st.session_state.error = "请求超时，请检查网络连接"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.session_state.error = "请求过于频繁，请稍后再试"
        else:
            st.session_state.error = f"API错误: {str(e)}"
    except (KeyError, ValueError) as e:
        st.session_state.error = f"数据解析错误: {str(e)}"
    except Exception as e:
        st.session_state.error = f"未知错误: {str(e)}"

def display_price():
    """显示价格信息"""
    # 自动刷新检查
    if (st.session_state.price_data and 
        time.time() - st.session_state.last_request > REFRESH_INTERVAL):
        with st.spinner("自动刷新数据中..."):
            fetch_bitcoin_data()
    
    if st.session_state.price_data:
        data = st.session_state.price_data
        change_class = "change-positive" if data['price_change_24h'] >= 0 else "change-negative"
        
        # 注入CSS样式
        st.markdown(PRICE_STYLE, unsafe_allow_html=True)
        
        # 主价格显示
        st.markdown(f"""
        <div class="price-display">
            <h1 class="price-value">${data['current_price']:,.2f}</h1>
            <p style="color: #666;">Bitcoin Price (USD)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 24小时变化
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <h3>24h Change</h3>
            <p style="font-size: 1.5rem;" class="{change_class}">
                ${data['price_change_24h']:,.2f} ({data['price_change_percentage_24h']:.2f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 更新时间
        st.caption(f"数据更新时间: {data['last_updated']}")
        st.caption(f"最后刷新: {st.session_state.last_updated}")

# ===== 页面布局 =====
st.title("₿ Bitcoin Price Tracker")
st.markdown(PRICE_STYLE, unsafe_allow_html=True)

# 刷新按钮
if st.button("🔄 手动刷新", key="refresh_btn"):
    with st.spinner("获取最新数据中..."):
        fetch_bitcoin_data()

# 错误显示
if st.session_state.error:
    st.error(st.session_state.error)
    if "频繁" in st.session_state.error:
        st.progress((time.time() - st.session_state.last_request) / RATE_LIMIT)

# 初始加载
if st.session_state.price_data is None:
    with st.spinner("初始化数据加载中..."):
        fetch_bitcoin_data()

# 显示价格
display_price()

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>数据来源: <a href="https://www.coingecko.com" target="_blank">CoinGecko API</a></p>
    <p>自动刷新间隔: {REFRESH_INTERVAL//60}分钟 | 请求间隔: {RATE_LIMIT}秒</p>
</div>
""".format(**locals()), unsafe_allow_html=True)