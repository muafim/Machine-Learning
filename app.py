from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prediksi')
def prediksi():
    return render_template('prediksi.html')

@app.route('/exchange')
def exchange():
    return render_template('exchange.html')

@app.route('/tentang')
def tentang():
    return render_template('tentang.html')

if __name__ == '__main__':
    app.run(debug=True)
