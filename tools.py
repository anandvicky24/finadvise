import yfinance as yf
import re
import requests
from requests import Session
from langchain_core.tools import tool

def clean_ticker(symbol: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9.]$', '', str(symbol).strip().upper())
    return cleaned.replace("'", "").replace('"', "")

def get_session():
    session = Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

@tool
def get_financial_data(ticker: str):
    """Fetch real-time price and news with rate-limit protection."""
    try:
        t = clean_ticker(ticker)
        # Use the custom session
        stock = yf.Ticker(t, session=get_session())
        
        # Adding a small delay or using 'fast_info' can also reduce the footprint
        price_data = stock.fast_info
        price = f"{price_data['last_price']:.2f}" if 'last_price' in price_data else "N/A"
        currency = price_data.get('currency', 'INR')
        
        # News is the heaviest call; we wrap it in a secondary try-block
        try:
            news_data = stock.news[:3]
            headlines = " | ".join([n.get('title') for n in news_data if isinstance(n.get('title'), str)])
        except:
            headlines = "News currently unavailable due to rate limits."

        return f"FETCHED_DATA for {t}: Price: {price} {currency}, News: {headlines}"
    except Exception as e:
        if "Too Many Requests" in str(e):
            return f"RATE_LIMIT_ERROR: Yahoo is throttling requests for {ticker}. Please wait 60 seconds."
        return f"Error for {ticker}: {str(e)}"
