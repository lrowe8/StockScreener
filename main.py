import datetime
import re
import yfinance as yf
import dash
from dash import dcc
from dash import html
import pandas as pd
import requests
import json

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

def update_graph(symbol:str, date_purchased:datetime, cost_per_share:float):
    # Set the timespan
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=(200 * 2))

    try:
        # Get stock data from yahoo
        df = yf.download(symbol, start, end)

        # Get the rolling averages
        df['20Day', symbol] = df['Close', symbol].rolling(20).mean()
        df['50Day', symbol] = df['Close', symbol].rolling(50).mean()
        df['200Day', symbol] = df['Close',symbol].rolling(200).mean()

        # Adjust start date to purchase date if needed
        if start < date_purchased:
            start = date_purchased

        # Get the maximum closing price of the stock after the start date
        max_price = df.loc[start : datetime.datetime.now()]['Close', symbol].max()

        # If the maximum price is lower than the purchase price then we want a line at 7% below purchase
        losing_sale_price = cost_per_share - (cost_per_share * .07)
        winning_sale_price = max_price - (max_price * .03)

        if winning_sale_price.item() >= cost_per_share:
            sale_price = (max_price - (max_price * .03)).item()
        else:
            sale_price = losing_sale_price
        
        df['SalePrice', symbol] = sale_price

        # Remove data older than 90 days
        df = df[df.index >= (datetime.datetime.now() - datetime.timedelta(days=90))]

        # Create the graph
        graph = dcc.Graph(
            id=f'graph-{symbol}', 
            figure= 
            {
                'data':[
                    {'x':df.index, 'y':df['Close', symbol], 'type':'line', 'name':symbol},
                    {'x':df.index, 'y':df['20Day', symbol], 'type':'line', 'name':'Short (20 Day)'},
                    {'x':df.index, 'y':df['50Day', symbol], 'type':'line', 'name':'Medium (50 Day)'},
                    {'x':df.index, 'y':df['200Day', symbol], 'type':'line', 'name':'Long (200 Day)'},
                    {'x':df.index, 'y':df['SalePrice', symbol], 'type':'line', 'name':'Sale Price'}
                    ],
                'layout':{
                    'title':symbol
                },
            },
            style = 
            {
                'border':f'2px {"tomato" if df.iloc[-1]["Close", symbol].item() < sale_price else "black"} solid',
            }
        )
    
    except Exception as e:
        print(e)
        graph = html.Div("Error retrieving stock data.")

    return graph

def get_tip_ranks(input_data: str):
    url = f'https://widgets.tipranks.com/api/widgets/stockAnalysisOverview/?tickers={input_data}'

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        json_result = json.loads(response.text)

        if json_result:
            blogger_sentiment = re.sub(r"(\w)([A-Z])", r"\1 \2", json_result[0]['bloggerConsensus'])
            news_sentiment = re.sub(r"(\w)([A-Z])", r"\1 \2", json_result[0]['newsSentiment'])
            investor_sentiment = re.sub(r"(\w)([A-Z])", r"\1 \2", json_result[0]['investorSentiment'])
            analyst_consensus = re.sub(r"(\w)([A-Z])", r"\1 \2", json_result[0]['analystConsensus'])
            insider_trend = re.sub(r"(\w)([A-Z])", r"\1 \2", json_result[0]['insiderTrend'])
            sma = re.sub(r"(\w)([A-Z])", r"\1 \2", json_result[0]['sma'])
            smart_score = json_result[0]['smartScore']
            investor_change_30_day = json_result[0]['investorHoldingChangeLast30Days']
            investor_change_7_day = json_result[0]['investorHoldingChangeLast7Days']
            fundamentals_return_on_equity = json_result[0]['fundamentalsReturnOnEquity']
            fundamentals_asset_growth = json_result[0]['fundamentalsAssetGrowth']
            color = 'green'

            if smart_score:
                if smart_score < 4:
                    color = 'tomato'
                elif smart_score < 7:
                    color = 'orange'
            else:
                smart_score = 'Smart score not available'
                color = 'black'

            results = html.Div(id=f'{input_data}-tip', children=[
                html.H4(f'Blogger Sentiment: {blogger_sentiment}'),
                html.H4(f'News Sentiment: {news_sentiment}'),
                html.H4(f'Investor Sentiment: {investor_sentiment}'),
                html.H4(f'Analyst Consensus: {analyst_consensus}'),
                html.H4(f'Insider Trend: {insider_trend}'),
                html.H4(f'Investor Holdings 7 Day Change: {investor_change_7_day}'),
                html.H4(f'Investor Holdings 30 Day Change: {investor_change_30_day}'),
                html.H4(f'Return on Equity: {fundamentals_return_on_equity}'),
                html.H4(f'Asset Growth: {fundamentals_asset_growth}'),
                html.H4(f'Simple Moving Average: {sma}'),
                html.H4(f'Smart Score: {smart_score}', style={'color': color}),
            ])
        else:
            results = html.Div("No tip ranks data.")
    else:
        results = html.Div("Error retrieving tip ranks data.")

    return results

# def get_sentiment(input_data:str):
#     date_str = datetime.datetime.now(datetime.UTC).isoformat().split('.')[0] + 'Z'
#     url = f'https://api-gw-prd.stocktwits.com/sentiment-api/{input_data}/detail?end={date_str}'

#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         json_result = json.loads(response.text)
#         message_volume = json_result['data']['messageVolume']['24h']['label'].replace('_', ' ')
#         sentiment = json_result['data']['sentiment']['24h']['label'].replace('_', ' ')

#         results = html.Div(id=f'{input_data}-twits', children=[
#             html.H4(f'Message Volume: {message_volume}'),
#             html.H4(f'Sentiment: {sentiment}')
#         ])
#     else:
#         results = html.Div("Error retrieving sentiment data.")

#     return results

def create_analyst(input_data:str):
    url = f'https://production.dataviz.cnn.io/quote/forecast/{input_data}'

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            json_result = json.loads(response.text)
            current_stock_price = json_result[0]['current_stock_price']
            high_color = 'green' if json_result[0]['high_target_price'] >= current_stock_price else 'tomato'
            median_color = 'green' if json_result[0]['median_target_price'] >= current_stock_price else 'tomato'
            low_color = 'green' if json_result[0]['low_target_price'] >= current_stock_price else 'tomato'

            results = html.Div(id=f'{input_data}-cnn', children=[
                html.H4(f'High: ${json_result[0]['high_target_price']:.2f} {json_result[0]['percent_high_price']:.2f}%', style={'color': high_color}),
                html.H4(f'Median: ${json_result[0]['median_target_price']:.2f} {json_result[0]['percent_median_price']:.2f}%', style={'color': median_color}),
                html.H4(f'Low: ${json_result[0]['low_target_price']:.2f} {json_result[0]['percent_low_price']:.2f}%', style={'color': low_color}),
            ])
        except Exception:
            results = html.Div("Error retrieving analyst data.")
    else:
        results = html.Div("Error retrieving analyst data.")

    return results


if __name__ == '__main__':
    stocks_xlsx = pd.read_excel('current-stocks.xlsx')
    # stocks_xlsx = pd.read_excel('stock-watchlist.xlsx')

    app = dash.Dash()
    app.title = "Stock Visualization"

    app.layout = html.Div(children=[
        html.H1("Stock Visualization Dashboard"),
    ])

    for _, record in stocks_xlsx.iterrows():
        app.layout.children += [html.Div(id=f'{record["Symbol"]}-graph', style={'padding-bottom': '20px'}), 
                                html.H3(f'{record["Symbol"]}'),
                                # get_sentiment(record["Symbol"]),
                                create_analyst(record["Symbol"]),
                                get_tip_ranks(record["Symbol"]),
                                update_graph(record["Symbol"], record["Date Purchased"], record["Cost Per Share"]),
                                ]    

    app.run_server()

    # app.layout = update_graph