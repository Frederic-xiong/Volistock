from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

def get_earnings_calendar():
    # You would need to implement an earnings calendar API here
    # Consider using Financial Modeling Prep or Alpha Vantage API
    pass

def get_earnings_surprise(ticker):
    stock = yf.Ticker(ticker)
    try:
        earnings = stock.earnings_history
        if len(earnings) > 0:
            return earnings.iloc[-1]['Surprise(%)']
    except:
        return 0
    return 0

def calculate_volatility_metrics(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period='60d')
        
        # Basic volatility metrics
        hist['Returns'] = hist['Close'].pct_change()
        volatility = hist['Returns'].std() * np.sqrt(252)
        
        # Technical indicators
        hist['SMA20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        
        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Options data for implied volatility
        options = stock.options
        if len(options) > 0:
            next_expiry = options[0]
            opt_chain = stock.option_chain(next_expiry)
            implied_vol = opt_chain.calls['impliedVolatility'].mean()
        else:
            implied_vol = 0

        # Get earnings data
        earnings_surprise = get_earnings_surprise(ticker_symbol)
        
        # Predict direction
        price_trend = 1 if hist['Close'].iloc[-1] > hist['SMA20'].iloc[-1] else -1
        
        return {
            'symbol': ticker_symbol,
            'historical_volatility': volatility,
            'implied_volatility': implied_vol,
            'rsi': rsi.iloc[-1],
            'earnings_surprise': earnings_surprise,
            'predicted_direction': price_trend,
            'current_price': hist['Close'].iloc[-1],
            'volume': hist['Volume'].iloc[-1],
            'volatility_score': (volatility * abs(earnings_surprise) * hist['Volume'].iloc[-1]/hist['Volume'].mean())
        }
    except Exception as e:
        print(f"Error processing {ticker_symbol}: {str(e)}")
        return None

@app.route('/api/volatile-stocks')
def get_volatile_stocks():
    # Major market stocks
    watchlist = ['AAPL', 'TSLA', 'NVDA', 'AMD', 'META', 'GOOGL', 'MSFT', 'AMZN', 
                 'NFLX', 'BA', 'JPM', 'GS', 'XOM', 'PFE', 'DIS', 'COIN', 'GME', 'AMC']
    
    results = []
    for symbol in watchlist:
        metrics = calculate_volatility_metrics(symbol)
        if metrics:
            results.append(metrics)
    
    # Sort by volatility score
    sorted_results = sorted(results, key=lambda x: x['volatility_score'], reverse=True)
    return jsonify(sorted_results[:5])

if __name__ == '__main__':
    app.run(debug=True)
