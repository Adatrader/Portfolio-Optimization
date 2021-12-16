from flask import Flask, render_template, jsonify, request
from flask_selfdoc import Autodoc
from helpers import get_historical_data, optimized_for_return, sharpe_ratio, optimized_for_volatility, min_volatility, optimized_for_return

app = Flask(__name__)
app.config["DEBUG"] = False  # TODO: Set to False during deployment
auto = Autodoc(app)


@app.route('/')
# Load landing page
def index():
    return render_template('index.html')


@auto.doc()
@app.route('/max_sharpe', methods=['POST'])
# POST for sharpe ratio
def max_sharpe():
    if(request.method == 'POST'):
        investment_amount = int(request.args.get('investment', 10000))

        # Get the configuration from JSON POST
        tickers = request.json["tickers"]
        # Generate historical data
        df = get_historical_data(tickers)
        # Calculate sharpe ratio and portfolio balance
        data = sharpe_ratio(df, investment_amount)
        return jsonify(data)
    return "Not post request", 400


@auto.doc()
@app.route('/target_return', methods=['POST'])
# POST for optimizing for target return %
def target_return():
    if(request.method == 'POST'):
        investment_amount = int(request.args.get('investment', 10000))
        target = float(request.args.get('return', 0.39))
        if (target > 0.4):
            target = float(0.39)
        # Get the configuration from JSON POST
        tickers = request.json["tickers"]
        # Generate historical data
        df = get_historical_data(tickers)
        data = optimized_for_return(df, investment_amount, target)
        return jsonify(data)
    else:
        return "Not post request", 400


@auto.doc()
@app.route('/efficient_risk', methods=['POST'])
# POST for optimizing for volatility
def efficient_risk():
    if(request.method == 'POST'):
        investment_amount = int(request.args.get('investment', 10000))
        # Get the configuration from JSON POST
        tickers = request.json["tickers"]
        # Generate historical data
        df = get_historical_data(tickers)
        # If target volitility less than 17% (infeasible), use min_volitility
        target_volatility = float(request.args.get('max_volatility', 0.15))
        if (target_volatility < 0.17):
            data = min_volatility(df, investment_amount)
        else:
            data = optimized_for_volatility(df, investment_amount, target_volatility)
        return jsonify(data)
    else:
        return "Not post request", 400


@app.route('/keep_alive', methods=['GET'])
# Keep alive for heroku 30 min sleep
def keep_alive():
    return jsonify({
        "status": "success"
    })


@app.route('/documentation')
def documentation():
    return auto.html()


# TODO: Comment out for heroku deployment
# if __name__ == "__main__":
#     app.run()
