import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
import requests
from plotly.subplots import make_subplots

st.set_page_config(page_title="我的投資組合", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .reportview-container {
        background: #F7F7F7
    }
    .main {
        background: #FFFFFF;
        padding: 2rem;
        border-radius: 0.5rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.1) !important;
    }
    .stMetric {
        background-color: #FFFFFF;
        border-radius: 0.3rem;
        padding: 1rem;
        box-shadow: 0 0.1rem 0.5rem 0 rgba(58, 59, 69, 0.1) !important;
    }
    .stDataFrame {
        border: none !important;
    }
    .stPlotlyChart {
        border-radius: 0.3rem;
        box-shadow: 0 0.1rem 0.5rem 0 rgba(58, 59, 69, 0.1) !important;
    }
    .stButton > button {
        width: 100%;
        background-color: #007AFF;
        color: white;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #ffffff;
        color: #007AFF;
        box-shadow: 0 0 10px rgba(0, 122, 255, 0.5);
    }

    /* 優化其他白色文字元素的懸浮效果 */
    .stSelectbox [data-baseweb="select"] div,
    .stMultiSelect [data-baseweb="select"] div,
    .stTextInput input,
    .stDateInput input,
    .stTimeInput input,
    .stNumberInput input {
        transition: all 0.3s ease;
    }

    .stSelectbox [data-baseweb="select"]:hover div,
    .stMultiSelect [data-baseweb="select"]:hover div,
    .stTextInput input:hover,
    .stDateInput input:hover,
    .stTimeInput input:hover,
    .stNumberInput input:hover {
        background-color: rgba(255, 255, 255, 0.1);
        box-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
    }

    /* 確保文本輸入框保持文本游標 */
    .stTextInput [data-baseweb="input"],
    .stTextInput [data-baseweb="input"] * {
        cursor: text !important;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

def load_portfolio():
    try:
        with open('my_portfolio.json', 'r', encoding='utf-8') as f:
            portfolio = json.load(f)
            # 簡單驗證載入的數據結構
            if all(isinstance(stock, dict) and 'Symbol' in stock and 'Name' in stock and 'Market' in stock and 'Transactions' in stock for stock in portfolio):
                return portfolio
            else:
                st.warning('載入的投資組合格式不正確,使用空投資組合')
                return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        st.warning('無法解析投資組合文件,使用空投資組合')
        return []

def save_portfolio():
    with open('my_portfolio.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.portfolio, f, ensure_ascii=False, indent=4)

st.session_state.portfolio = load_portfolio()

def get_current_price(symbol, market):
    try:
        if market == '美股':
            ticker = yf.Ticker(symbol)
        else:  # 台股
            ticker = yf.Ticker(f"{symbol}.TW")
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            return None
    except Exception as e:
        st.error(f"獲取 {symbol} 價格時發生錯誤: {str(e)}")
        return None

def get_usd_to_twd_rate():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        return data['rates']['TWD']
    except Exception as e:
        st.error(f"獲取匯率時發生錯誤: {str(e)}")
        return 30  # 使用預設匯率

def calculate_performance():
    performance = []
    usd_to_twd_rate = get_usd_to_twd_rate()
    
    for stock in st.session_state.portfolio:
        symbol = stock['Symbol']
        market = stock['Market']
        
        current_price = get_current_price(symbol, market)
        
        if current_price is not None:
            total_quantity = sum(transaction['Quantity'] for transaction in stock['Transactions'])
            total_cost = sum(transaction['Buy Price'] * transaction['Quantity'] for transaction in stock['Transactions'])
            average_buy_price = total_cost / total_quantity if total_quantity > 0 else 0
            
            current_value = current_price * total_quantity
            profit_loss = current_value - total_cost
            performance_pct = (profit_loss / total_cost) * 100 if total_cost != 0 else 0

            # 轉換為台幣
            if market == '美股':
                current_value *= usd_to_twd_rate
                total_cost *= usd_to_twd_rate
                profit_loss *= usd_to_twd_rate

            performance.append({
                'Symbol': symbol,
                'Name': stock['Name'],
                'Market': market,
                'Total Quantity': total_quantity,
                'Average Buy Price': f"{'US$' if market == '美股' else 'NT$'}{average_buy_price:.2f}",
                'Current Price': f"{'US$' if market == '美股' else 'NT$'}{current_price:.2f}",
                'Current Value (TWD)': current_value,
                'Total Cost (TWD)': total_cost,
                'Profit/Loss (TWD)': profit_loss,
                'Performance %': performance_pct
            })
        else:
            st.warning(f"無法獲取 {symbol} 的當前價格，已從性能計算中排除。")
    
    return pd.DataFrame(performance)

tech_color_scheme = [
    '#007AFF',  # 藍色
    '#5856D6',  # 紫色
    '#FF9500',  # 橙色
    '#FFCC00',  # 黃色
    '#00C7BE',  # 青色
    '#AF52DE',  # 淺紫色
    '#8E8E93',  # 灰色
    '#FF2D55',  # 珊瑚紅
    '#64D2FF',  # 天藍色
    '#5AC8FA'   # 淺藍色
]

def create_distribution_chart(performance):
    fig_distribution = px.pie(
        performance, 
        values='Current Value (TWD)', 
        names='Symbol', 
        title='投資金額占比',
        color_discrete_sequence=tech_color_scheme,
        hole=0.4
    )
    fig_distribution.update_traces(textposition='inside', textinfo='percent+label')
    fig_distribution.update_layout(
        height=400, 
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333333'),
        title_font_size=18,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    return fig_distribution

def create_profit_loss_chart(data, title, value_column='Profit/Loss', is_percentage=False):
    data_sorted = data.sort_values(value_column, ascending=True)
    
    colors = ['#34C759' if x < 0 else '#FF3B30' for x in data_sorted[value_column]]
    
    fig = go.Figure(go.Bar(
        x=data_sorted['Symbol'],
        y=data_sorted[value_column],
        marker_color=colors,
        text=data_sorted[value_column].apply(lambda x: f'{x:.2f}%' if is_percentage else f'${x:,.2f}'),
        textposition='outside',
        textfont=dict(size=10, color='#333333'),
    ))
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, color='#333333')
        ),
        xaxis_title='股票代號',
        yaxis_title='收益率 (%)' if is_percentage else '收益/虧損',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333333'),
        yaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor='#333333', gridcolor='#E0E0E0'),
        xaxis=dict(gridcolor='#E0E0E0'),
        margin=dict(l=20, r=20, t=40, b=20, pad=4),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        bargap=0.2
    )
    
    fig.update_xaxes(type='category', tickangle=45)
    fig.update_yaxes(automargin=True)
    
    y_max = max(abs(data_sorted[value_column].min()), abs(data_sorted[value_column].max()))
    fig.update_yaxes(range=[-y_max*1.15, y_max*1.15])
    
    return fig

def get_stock_history(symbol, market, period='6mo'):
    try:
        if market == '美股':
            ticker = yf.Ticker(symbol)
        else:  # 台股
            ticker = yf.Ticker(f"{symbol}.TW")
        history = ticker.history(period=period)
        history['Six_Month_Avg'] = history['Close'].mean()  # 計算半年均價
        return history
    except Exception as e:
        st.error(f"獲取 {symbol} 歷史數據時發生錯誤: {str(e)}")
        return None

def create_six_month_chart(portfolio):
    fig = make_subplots(rows=len(portfolio), cols=1, subplot_titles=[f"{stock['Symbol']} - {stock['Name']}" for stock in portfolio])
    
    for i, stock in enumerate(portfolio, start=1):
        history = get_stock_history(stock['Symbol'], stock['Market'])
        if history is not None and not history.empty:
            fig.add_trace(
                go.Scatter(x=history.index, y=history['Close'], name=stock['Symbol']),
                row=i, col=1
            )
    
    fig.update_layout(
        height=300*len(portfolio),
        title_text="半年股價走勢",
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black')
    )
    fig.update_xaxes(rangeslider_visible=False)
    for i in range(1, len(portfolio)+1):
        fig.update_yaxes(title_text="價格", row=i, col=1)
    
    return fig

st.title('我的韭菜日記')

# 側邊欄
with st.sidebar:
    st.header('管理投資組合')
    
    with st.expander("添加新股票", expanded=False):
        with st.form("add_stock_form"):
            symbol = st.text_input('股票代號').upper()
            name = st.text_input('股票名稱')
            market = st.selectbox('市場', ['美股', '台股'])
            buy_date = st.date_input('購買日期', max_value=datetime.now().date())
            buy_price = st.number_input('購買價格', min_value=0.01, step=0.01)
            quantity = st.number_input('購買數量', min_value=1, step=1)
            submitted = st.form_submit_button('添加股票')
            if submitted:
                new_stock = {
                    'Symbol': symbol,
                    'Name': name,
                    'Market': market,
                    'Transactions': [
                        {
                            'Buy Date': buy_date.strftime('%Y-%m-%d'),
                            'Buy Price': buy_price,
                            'Quantity': quantity
                        }
                    ]
                }
                
                # 檢查相同的股票
                existing_stock = next((stock for stock in st.session_state.portfolio if stock['Symbol'] == symbol), None)
                if existing_stock:
                    existing_stock['Transactions'].append(new_stock['Transactions'][0])
                else:
                    st.session_state.portfolio.append(new_stock)
                
                save_portfolio()
                st.success('已成功添加票')
                st.rerun()
    
    if st.session_state.portfolio:
        with st.expander("刪除交易", expanded=False):
            stock_to_delete = st.selectbox('選擇要刪除交易的股票', [f"{stock['Symbol']} - {stock['Name']}" for stock in st.session_state.portfolio])
            if stock_to_delete:
                symbol_to_delete = stock_to_delete.split(' - ')[0]
                selected_stock = next((stock for stock in st.session_state.portfolio if stock['Symbol'] == symbol_to_delete), None)
                
                if selected_stock and selected_stock['Transactions']:
                    transaction_options = [f"{t['Buy Date']} - 數: {t['Quantity']} - 價格: {t['Buy Price']}" for t in selected_stock['Transactions']]
                    transaction_to_delete = st.selectbox('選擇要刪除的交易', transaction_options)
                    
                    if transaction_to_delete and st.button('刪除選中的交易', key='delete_transaction_button'):
                        index_to_delete = transaction_options.index(transaction_to_delete)
                        del selected_stock['Transactions'][index_to_delete]
                        
                        if not selected_stock['Transactions']:
                            st.session_state.portfolio = [stock for stock in st.session_state.portfolio if stock['Symbol'] != symbol_to_delete]
                        
                        save_portfolio()
                        st.success(f'已刪除 {stock_to_delete} 的交易：{transaction_to_delete}')
                        st.rerun()
                else:
                    st.info('該股票沒有交易記錄')

    if st.button("儲存投資組合", key="save_portfolio_button"):
        save_portfolio()
        st.success('已成功儲存投資組合')

# 主要內容區
if st.session_state.portfolio:
    performance = calculate_performance()
    
    if not performance.empty:
        # 獲取匯率
        usd_to_twd_rate = get_usd_to_twd_rate()
        
        # 顯示總體概況
        total_investment = performance['Total Cost (TWD)'].sum()
        total_current_value = performance['Current Value (TWD)'].sum()
        total_profit_loss = performance['Profit/Loss (TWD)'].sum()
        total_performance = (total_profit_loss / total_investment) * 100 if total_investment != 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("總投資", f"NT${total_investment:,.0f}")
        col2.metric("當前價值", f"NT${total_current_value:,.0f}")
        col3.metric("總收益", f"NT${total_profit_loss:,.0f}", f"{total_performance:.2f}%", delta_color="inverse")

        # 顯示匯率資訊
        st.markdown(f"<div style='text-align: right; color: gray; font-size: 0.8em;'>當前匯率：1 USD = {usd_to_twd_rate:.2f} TWD</div>", unsafe_allow_html=True)

        st.subheader('投資組合分析')

        # 其他三個圖表分兩行顯示
        col1, col2 = st.columns(2)

        with col1:
            fig_distribution = create_distribution_chart(performance)
            st.plotly_chart(fig_distribution, use_container_width=True)

        with col2:
            fig_absolute = create_profit_loss_chart(performance, title='股票收益/虧損金額', value_column='Profit/Loss (TWD)')
            fig_absolute.update_layout(height=400)
            st.plotly_chart(fig_absolute, use_container_width=True)

        fig_percentage = create_profit_loss_chart(performance, title='股票收益率', value_column='Performance %', is_percentage=True)
        fig_percentage.update_layout(height=400)
        st.plotly_chart(fig_percentage, use_container_width=True)

        # 半年股價走勢分析 (佔據整行)
        st.subheader('半年股價走勢分析')
        stock_options = [f"{stock['Symbol']} - {stock['Name']}" for stock in st.session_state.portfolio]
        selected_stock = st.selectbox('選擇股票查看半年走勢', stock_options)

        selected_symbol = selected_stock.split(' - ')[0]
        selected_stock_info = next((stock for stock in st.session_state.portfolio if stock['Symbol'] == selected_symbol), None)

        if selected_stock_info:
            history = get_stock_history(selected_stock_info['Symbol'], selected_stock_info['Market'])
            if history is not None and not history.empty:
                # 計算平均買入價格
                total_quantity = sum(transaction['Quantity'] for transaction in selected_stock_info['Transactions'])
                total_cost = sum(transaction['Buy Price'] * transaction['Quantity'] for transaction in selected_stock_info['Transactions'])
                average_buy_price = total_cost / total_quantity if total_quantity > 0 else 0

                # 確定貨幣單位
                currency = 'US$' if selected_stock_info['Market'] == '美股' else 'NT$'

                # 創建子圖
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])

                # 添加價格線
                fig.add_trace(go.Scatter(
                    x=history.index, 
                    y=history['Close'], 
                    mode='lines', 
                    name='收盤價',
                    line=dict(color=tech_color_scheme[2], width=2)
                ), row=1, col=1)

                # 添加平均買入價格線
                fig.add_trace(go.Scatter(
                    x=[history.index[0], history.index[-1]],
                    y=[average_buy_price, average_buy_price],
                    mode='lines',
                    name='平均買入價格',
                    line=dict(color=tech_color_scheme[3], dash='dash', width=3)
                ), row=1, col=1)

                # 添加半年均價線
                fig.add_trace(go.Scatter(
                    x=[history.index[0], history.index[-1]],
                    y=[history['Six_Month_Avg'].iloc[0], history['Six_Month_Avg'].iloc[0]],
                    mode='lines',
                    name='半年均價',
                    line=dict(color=tech_color_scheme[4], dash='dot', width=3)
                ), row=1, col=1)

                # 添加最高價和最低價標記
                highest_price = history['Close'].max()
                lowest_price = history['Close'].min()
                highest_date = history['Close'].idxmax()
                lowest_date = history['Close'].idxmin()

                fig.add_trace(go.Scatter(
                    x=[highest_date],
                    y=[highest_price],
                    mode='markers+text',
                    name='最高價',
                    text=[f'${highest_price:.2f}'],
                    textposition='top center',
                    marker=dict(color=tech_color_scheme[6], size=10, symbol='triangle-up'),
                    showlegend=False
                ), row=1, col=1)

                fig.add_trace(go.Scatter(
                    x=[lowest_date],
                    y=[lowest_price],
                    mode='markers+text',
                    name='最低價',
                    text=[f'${lowest_price:.2f}'],
                    textposition='bottom center',
                    marker=dict(color=tech_color_scheme[1], size=10, symbol='triangle-down'),
                    showlegend=False
                ), row=1, col=1)

                # 添加成交量圖
                fig.add_trace(go.Bar(
                    x=history.index,
                    y=history['Volume'],
                    name='成交量',
                    marker_color=tech_color_scheme[3],
                    opacity=0.7
                ), row=2, col=1)

                # 調整y軸範圍
                y_min = min(history['Close'].min(), average_buy_price, history['Six_Month_Avg'].iloc[0])
                y_max = max(history['Close'].max(), average_buy_price, history['Six_Month_Avg'].iloc[0])
                y_range = y_max - y_min
                y_padding = y_range * 0.15  # 增加15%的空間

                fig.update_layout(
                    title=f"{selected_stock} 半年走勢與成交量",
                    height=500,  # 增加圖表高度
                    margin=dict(l=20, r=20, t=40, b=100),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(color='black'),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5,
                        bgcolor="rgba(255,255,255,0.5)",  # 半透明背景
                        bordercolor="rgba(0,0,0,0.1)",    # 淺灰色邊框
                        borderwidth=1
                    ),
                    yaxis=dict(range=[y_min - y_padding, y_max + y_padding])  # 設置新的y軸範圍
                )

                # 更新子圖的標題和軸標籤
                fig.update_xaxes(title_text="日期", row=2, col=1)
                fig.update_yaxes(title_text="價格", row=1, col=1)
                fig.update_yaxes(title_text="成交量", row=2, col=1)

                # 添加註釋來標記平均買入價格和半年均價
                fig.add_annotation(
                    x=history.index[-1],
                    y=average_buy_price,
                    text=f"平均買入價格: {currency}{average_buy_price:.2f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=tech_color_scheme[3],
                    ax=50,
                    ay=-30,
                    row=1, col=1
                )
                fig.add_annotation(
                    x=history.index[-1],
                    y=history['Six_Month_Avg'].iloc[0],
                    text=f"半年均價: {currency}{history['Six_Month_Avg'].iloc[0]:.2f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=tech_color_scheme[4],
                    ax=50,
                    ay=30,
                    row=1, col=1
                )

                st.plotly_chart(fig, use_container_width=True)

                # 將買入均價和半年均價資訊並排顯示
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<div style='text-align: center;'><p style='background-color: #E6F3FF; padding: 10px; border-radius: 5px;'>平均買入價格: {currency}{average_buy_price:.2f}</p></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div style='text-align: center;'><p style='background-color: #E6F3FF; padding: 10px; border-radius: 5px;'>半年均價: {currency}{history['Six_Month_Avg'].iloc[0]:.2f}</p></div>", unsafe_allow_html=True)
            else:
                st.warning(f"無法獲取 {selected_stock} 的歷史數據")
        else:
            st.warning("請選擇一支股票")

        # 顯示詳細的投資組合表格
        with st.expander("投資組合詳情", expanded=False):
            st.subheader('投資組合詳情')
            
            def color_profit_loss(val):
                color = '#FF3B30' if val > 0 else '#34C759'
                return f'color: {color}'

            styled_df = performance[['Symbol', 'Name', 'Market', 'Total Quantity', 'Average Buy Price', 'Current Price', 'Current Value (TWD)', 'Profit/Loss (TWD)', 'Performance %']].style.format({
                'Total Quantity': '{:,.0f}',
                'Average Buy Price': lambda x: x,  # 保持原樣,因為已經在calculate_performance中格式化
                'Current Price': lambda x: x,  # 保持原樣,因為已經在calculate_performance中格式化
                'Current Value (TWD)': 'NT${:,.0f}',
                'Profit/Loss (TWD)': 'NT${:,.0f}',
                'Performance %': '{:.2f}%'
            }).map(color_profit_loss, subset=['Profit/Loss (TWD)', 'Performance %'])
            
            st.dataframe(styled_df, hide_index=True, height=400)

        # 顯示每支股票的詳細購買記錄
        with st.expander("查看詳細購買記錄", expanded=False):
            for stock in st.session_state.portfolio:
                st.subheader(f"{stock['Name']} ({stock['Symbol']})")
                transactions_df = pd.DataFrame(stock['Transactions'])
                st.dataframe(
                    transactions_df.style.format({
                        'Buy Price': '${:.2f}',
                        'Quantity': '{:,.0f}'
                    }),
                    hide_index=True
                )

    else:
        st.info('您的投資組合目前為空。請使用側邊欄添加股票。')