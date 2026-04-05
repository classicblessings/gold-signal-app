import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(layout="wide")

# ===== AUTO REFRESH (SAFE) =====
st.markdown(
    """
    <meta http-equiv="refresh" content="10">
    """,
    unsafe_allow_html=True
)

# ===== STYLE =====
st.markdown("""
<style>
body {background-color:#0e0e0e;}

.signal-box {
    text-align:center;
    font-size:65px;
    font-weight:bold;
    padding:25px;
    border-radius:20px;
    margin-top:30px;
}

.buy {background:#00c853;color:white;}
.sell {background:#ff1744;color:white;}
.wait {background:#2c2c2c;color:#aaa;}

.timer
