"""
Streamlit UI for ORB Screener
File: streamlit_ui.py
FIXED: Handles backend response correctly
"""

import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="ORB Institutional Screener",
    layout="wide"
)

st.title("🚀 ORB Institutional Screener")

# ---------------- Backend Status ----------------
try:
    status = requests.get(f"{BACKEND_URL}/", timeout=5).json()
    st.success(f"✓ Backend Connected | {status['app']} v{status['version']}")
    
    # Show connection details
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Baseline Loaded", "✓" if status.get('baseline_loaded') else "✗")
    with col2:
        st.metric("Baseline Symbols", status.get('baseline_symbols', 0))
    with col3:
        st.metric("Stream Connected", "✓" if status.get('stream_connected') else "✗")
        
except requests.exceptions.RequestException as e:
    st.error("❌ Backend not running on http://localhost:8000")
    st.info("Start backend with: `python run.py`")
    st.stop()

st.divider()

# ---------------- Fetch Signals ----------------
def fetch_signals():
    try:
        response = requests.get(f"{BACKEND_URL}/api/top-signals", timeout=5).json()
        return response.get('signals', [])
    except Exception as e:
        st.error(f"Error fetching signals: {e}")
        return []

signals = fetch_signals()

# ---------------- Layout ----------------
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 Live ORB Signals")

    if signals:
        # Convert to DataFrame
        df = pd.DataFrame(signals)
        
        # Check what columns we actually have
        available_columns = df.columns.tolist()
        
        # Map backend column names to display names
        column_mapping = {
            'rank': 'Rank',
            'symbol': 'Symbol',
            'dir': 'Direction',
            'price': 'Price',
            'change_percent': 'Change %',
            'volume': 'Volume',
            'volume_heat_percent': 'Vol Heat %',
            'value': 'Value (Cr)',
            'value_heat_percent': 'Val Heat %',
            'body': 'Body',
            'orb_valid': 'ORB',
            'speed_minutes': 'Speed',
            'score': 'Score',
            'time': 'Time'
        }
        
        # Select only columns that exist
        display_columns = []
        for backend_col, display_name in column_mapping.items():
            if backend_col in available_columns:
                display_columns.append(backend_col)
        
        if not display_columns:
            st.warning("⚠️ No valid columns in backend response")
            st.json(signals[0] if signals else {})
        else:
            # Create display DataFrame
            table_df = df[display_columns].copy()
            
            # Rename columns for display
            table_df.columns = [column_mapping.get(col, col) for col in display_columns]
            
            # Format numeric columns
            if 'Price' in table_df.columns:
                table_df['Price'] = table_df['Price'].apply(lambda x: f"₹{float(x):,.2f}")
            
            if 'Change %' in table_df.columns:
                table_df['Change %'] = table_df['Change %'].apply(lambda x: f"{float(x):+.2f}%")
            
            if 'Score' in table_df.columns:
                table_df['Score'] = table_df['Score'].astype(int)
            
            # Style the dataframe
            def highlight_score(row):
                if 'Score' not in row.index:
                    return [''] * len(row)
                    
                score = row['Score']
                if score >= 90:
                    color = 'background-color: #10b981; color: white'
                elif score >= 80:
                    color = 'background-color: #84cc16; color: white'
                elif score >= 70:
                    color = 'background-color: #eab308; color: black'
                else:
                    color = 'background-color: #6b7280; color: white'
                
                colors = [''] * len(row)
                if 'Score' in row.index:
                    colors[list(row.index).index('Score')] = color
                return colors
            
            # Display styled table
            st.dataframe(
                table_df.style.apply(highlight_score, axis=1),
                use_container_width=True,
                height=400
            )

            # -------- Top Stock Chart --------
            if len(df) > 0:
                top_stock = df.iloc[0]
                
                if 'sparkline' in top_stock and top_stock['sparkline']:
                    st.subheader(f"📈 {top_stock['symbol']} - Price Movement")
                    
                    sparkline_data = top_stock['sparkline']
                    
                    if isinstance(sparkline_data, list) and len(sparkline_data) > 0:
                        chart_df = pd.DataFrame({
                            'Index': list(range(len(sparkline_data))),
                            'Price': sparkline_data
                        })

                        fig = go.Figure()

                        fig.add_trace(go.Scatter(
                            x=chart_df['Index'],
                            y=chart_df['Price'],
                            mode='lines+markers',
                            line=dict(width=3, color='#10b981'),
                            marker=dict(size=6),
                            name=top_stock['symbol']
                        ))

                        fig.update_layout(
                            height=300,
                            margin=dict(l=10, r=10, t=30, b=10),
                            xaxis_title="Time Period",
                            yaxis_title="Price",
                            template="plotly_dark",
                            showlegend=False
                        )

                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Sparkline data not available yet")

    else:
        st.info("⏳ Waiting for ORB signals...")
        st.write("**Signals will appear when:**")
        st.write("1. Market is open (9:15 AM onwards)")
        st.write("2. Stocks break their 5-minute ORB (Opening Range)")
        st.write("3. Volume/Value/Body meet threshold criteria")
        st.write("4. Score > 80")

with col2:
    st.subheader("🔧 System Status")
    st.json(status)
    
    st.divider()
    
    st.subheader("📋 Legend")
    st.markdown("""
    **Score Colors:**
    - 🟢 90+ : Strong Signal
    - 🟢 80-89 : Good Signal
    - 🟡 70-79 : Moderate
    - ⚪ <70 : Weak
    
    **Direction:**
    - LONG: Buy above ORB high
    - SHORT: Sell below ORB low
    """)

# Auto-refresh every 3 seconds
st.caption("🔄 Auto-refresh every 3 seconds")
time.sleep(3)
st.rerun()