from flask import Flask, render_template, jsonify, request
import requests
import time
import logging

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/exchange')
def exchange():
    return render_template('exchange.html')

@app.route('/prediksi')
def prediksi():
    return render_template('prediksi.html')

@app.route('/tentang')
def tentang():
    return render_template('tentang.html')

@app.route('/coin/<symbol>')
def coin(symbol):
    # Halaman chart untuk koin tertentu
    return render_template('coin.html', symbol=symbol.upper())

@app.route('/api/binance')
def api_binance():
    return jsonify(fetch_binance_data())

@app.route('/api/klines')
def api_klines():
    # Parameter: symbol (tanpa USDT), interval (1m,15m,30m,1h,1d,1w,1M)
    symbol = request.args.get('symbol', '').upper()
    interval = request.args.get('interval', '15m')
    if not symbol:
        return jsonify({'error': 'Missing symbol'}), 400

    binance_symbol = f"{symbol}USDT"
    params = {'symbol': binance_symbol, 'interval': interval, 'limit': 500}
    try:
        resp = requests.get('https://api.binance.com/api/v3/klines', params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        logging.error(f"Error fetching klines: {e}")
        return jsonify({'error': str(e)}), 500

    ohlc = []
    for item in raw:
        ohlc.append({
            'x': item[0],  # timestamp (ms UTC)
            'open': float(item[1]),
            'high': float(item[2]),
            'low': float(item[3]),
            'close': float(item[4])
        })
    return jsonify(ohlc)


def fetch_binance_data():
    try:
        resp = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        logging.error(f"Binance API error: {e}")
        return []

    coins = []
    for item in raw:
        sym = item.get('symbol', '')
        if not sym.endswith('USDT'):
            continue
        try:
            base = sym[:-4].upper()
            coins.append({
                'symbol': base,
                'price': float(item['lastPrice']),
                'change_pct': float(item['priceChangePercent']),
                'volume': float(item['quoteVolume']),
            })
        except:
            continue

    coins.sort(key=lambda x: x['volume'], reverse=True)

    gecko_caps = {}
    for page in [1, 2]:
        try:
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 250,
                'page': page,
                'sparkline': 'false'
            }
            r = requests.get('https://api.coingecko.com/api/v3/coins/markets', params=params, timeout=10)
            r.raise_for_status()
            for c in r.json():
                gecko_caps[c['symbol'].upper()] = c.get('market_cap', None)
            time.sleep(1)
        except Exception as e:
            logging.warning(f"CoinGecko page {page} failed: {e}")

    for c in coins:
        c['market_cap'] = gecko_caps.get(c['symbol'], None)
    for i, c in enumerate(coins, start=1):
        c['rank'] = i

    return coins

if __name__ == '__main__':
    app.run(debug=True)