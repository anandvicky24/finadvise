import yfinance as yf
import re
from langchain_core.tools import tool

def clean_ticker(symbol: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9.]$', '', str(symbol).strip().upper())
    return cleaned.replace("'", "").replace('"', "")

@tool
def get_financial_data(ticker: str):
    """Fetch real-time price and news and headlines."""
    try:
        t = clean_ticker(ticker)
        stock = yf.Ticker(t)
        hist = stock.history(period="1d")
        price = f"{hist['Close'].iloc[-1]:.2f}" if not hist.empty else "N/A"
        currency = stock.info.get('currency', 'INR')
        news_data = stock.news[:3]
        headlines = " | ".join([n.get('title') for n in news_data if isinstance(n.get('title'), str)])
        return f"{t}: Price: {price} {currency}, News: {headlines or 'No news'}"
    except Exception as e:
        return f"Error for {ticker}: {str(e)}"

tools = [get_financial_data]