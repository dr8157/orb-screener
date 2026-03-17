import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import asyncio
import websockets
import json

st.set_page_config(page_title="ORB Screener Dashboard", layout="wide")
st.title("ORB Institutional Screener Dashboard")

# Placeholder for live table
placeholder = st.empty()

# Function to draw sparkline chart
def plot_sparkline(data):
    fig, ax = plt.subplots(figsize=(3, 0.8))
    ax.plot(data, color="green")
    ax.axis("off")
    return fig

# Async function to listen to WebSocket
async def ws_listen():
    uri = "ws://localhost:8000/ws/stream"
    async with websockets.connect(uri) as ws:
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get("type") == "update":
                signals = data.get("signals", [])
                if not signals:
                    placeholder.write("No signals yet...")
                else:
                    # Prepare DataFrame
                    df = pd.DataFrame(signals)
                    df = df[["rank","symbol","dir","price","score","sparkline"]]

                    # Color-code LONG/SHORT
                    df['dir_color'] = df['dir'].map({"LONG":"🟢 LONG", "SHORT":"🔴 SHORT"})

                    # Show table
                    table_df = df[["rank","symbol","dir_color","price","score"]]
                    placeholder.table(table_df)

                    # Sparklines
                    st.subheader("Price Sparklines")
                    cols = st.columns(len(df))
                    for i, col in enumerate(cols):
                        if i < len(df):
                            col.write(f"{df.iloc[i]['symbol']} ({df.iloc[i]['dir']})")
                            spark = df.iloc[i]['sparkline']
                            if spark:
                                col.pyplot(plot_sparkline(spark))

# Run the WebSocket listener
asyncio.run(ws_listen())
