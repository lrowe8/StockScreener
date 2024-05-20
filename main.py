import datetime
import yfinance as yf
import dash
from dash import dcc
from dash import html
import csv
import requests
import json

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

def update_graph(input_data:str):
    # Set the timespan
    # start = datetime.datetime(2010, 1, 1)
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=(365 * 2))

    try:
        # Get stock data from yahoo
        df = yf.download(input_data, start, end)

        # Get the rolling averages
        df['20Day'] = df['Close'].rolling(20).mean()
        df['50Day'] = df['Close'].rolling(50).mean()
        df['200Day'] = df['Close'].rolling(200).mean()

        # Remove data older than 90 days
        df = df[df.index >= (datetime.datetime.now() - datetime.timedelta(days=90))]

        # Create the graph
        graph = dcc.Graph(
            id=f'graph-{input_data}', 
            figure = 
            {
                'data':[
                    {'x':df.index, 'y':df.Close, 'type':'line', 'name':input_data},
                    {'x':df.index, 'y':df['20Day'], 'type':'line', 'name':'Short (20 Day)'},
                    {'x':df.index, 'y':df['50Day'], 'type':'line', 'name':'Medium (50 Day)'},
                    {'x':df.index, 'y':df['200Day'], 'type':'line', 'name':'Long (200 Day)'}
                    ],
                'layout':{
                    'title':input_data
                },
            },
            style = 
            {
                'border':'2px black solid',
            }
        )
    
    except Exception as e:
        graph = html.Div("Error retrieving stock data.")

    return graph

def get_sentiment(input_data:str):
    date_str = datetime.datetime.now(datetime.UTC).isoformat().split('.')[0] + 'Z'
    url = f'https://api-gw-prd.stocktwits.com/sentiment-api/{input_data}/detail?end={date_str}'

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        json_result = json.loads(response.text)
        message_volume = json_result['data']['messageVolume']['24h']['label'].replace('_', ' ')
        sentiment = json_result['data']['sentiment']['24h']['label'].replace('_', ' ')

        results = html.Div(id=f'{input_data}-twits', children=[
            html.H4(f'Message Volume: {message_volume}'),
            html.H4(f'Sentiment: {sentiment}')
        ])
    else:
        results = html.Div("Error retrieving sentiment data.")

    return results

def create_analyst(input_data:str):
    url = f'https://production.dataviz.cnn.io/quote/forecast/{input_data}'

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
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
    else:
        results = html.Div("Error retrieving analyst data.")

    return results


if __name__ == '__main__':
    rows = []
    with open('current_stocks.csv') as csvfile:
        current_stocks = csv.DictReader(csvfile)
        
        for row in current_stocks:
            rows.append(row)

    app = dash.Dash()
    app.title = "Stock Visualization"

    app.layout = html.Div(children=[
        html.H1("Stock Visualization Dashboard"),
    ])

    for row in rows:
        app.layout.children += [html.Div(id=f'{row["Symbol"]}-graph', style={'padding-bottom': '20px'}), 
                                get_sentiment(row["Symbol"]),
                                create_analyst(row["Symbol"]),
                                update_graph(row["Symbol"]),
                                ]    

    app.run_server()

    # app.layout = update_graph