from flask import Flask, render_template, jsonify
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


def fetch_binance_data():
    # 1. Ambil data 24hr ticker Binance
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

    # sort by volume desc
    coins.sort(key=lambda x: x['volume'], reverse=True)

    # 2. Ambil market cap dari CoinGecko: top 500 lewat 2 halaman
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
                # symbol di CoinGecko adalah ticker lowercase, e.g. "btc"
                gecko_caps[c['symbol'].upper()] = c.get('market_cap', None)
            time.sleep(1)  # hindari rate limit
        except Exception as e:
            logging.warning(f"CoinGecko page {page} failed: {e}")

    # 3. Gabungkan market cap
    for c in coins:
        c['market_cap'] = gecko_caps.get(c['symbol'], None)

    # 4. Set rank ulang
    for i, c in enumerate(coins, start=1):
        c['rank'] = i

    return coins


@app.route('/api/binance')
def api_binance():
    return jsonify(fetch_binance_data())


if __name__ == '__main__':
    app.run(debug=True)
