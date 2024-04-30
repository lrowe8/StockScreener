import datetime
import yfinance as yf
import dash
from dash import dcc
from dash import html
import csv

def update_graph(input_data:str):
    # Set the timespan
    start = datetime.datetime(2010, 1, 1)
    end = datetime.datetime.now()

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
        app.layout.children += [html.Div(id=f'{row["Symbol"]}-graph', style={'padding-bottom': '20px'}), update_graph(row["Symbol"])]    

    app.run_server()

    # app.layout = update_graph