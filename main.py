import datetime
import yfinance as yf
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash()
app.title = "Stock Visualization"

app.layout = html.Div(children=[
    html.H1("Stock Visualization Dashboard"),
    html.H4("Please enter the stock name"),
    dcc.Input(id='input', value='INTC', type='text'),
    html.Div(id='output-graph')
])

@app.callback(
    Output(component_id='output-graph', component_property='children'),
    [Input(component_id='input', component_property='value')]
)
def update_graph(input_data):
    # Set the timespan
    start = datetime.datetime(2010, 1, 1)
    end = datetime.datetime.now()

    try:
        # Get stock data from yahoo
        df = yf.download(input_data, start, end)

        # Get the rolling averages
        df['5Day'] = df['Close'].rolling(5).mean()
        df['40Day'] = df['Close'].rolling(40).mean()
        df['Converge'] = (df['40Day'] - df['5Day']).abs()

        # Remove data older than 90 days
        df = df[df.index >= (datetime.datetime.now() - datetime.timedelta(days=90))]

        # Convergance check
        converge = df['Converge'].iloc[-4:]
        increasing = all([v >= converge.iloc[i - 1] for i, v in enumerate(converge.iloc[1:], 1)])
        decreasing = all([converge.iloc[i - 1] >= v for i, v in enumerate(converge.iloc[1:], 1)])

        color = 'black'
        if increasing and not decreasing:
            color = 'MediumSeaGreen'
        elif decreasing and not increasing:
            color = 'Tomato'

        # Create the graph
        graph = dcc.Graph(
            id='example', 
            figure = 
            {
                'data':[
                    {'x':df.index, 'y':df.Close, 'type':'line', 'name':input_data},
                    {'x':df.index, 'y':df['5Day'], 'type':'line', 'name':'5 Day Avg'},
                    {'x':df.index, 'y':df['40Day'], 'type':'line', 'name':'40 Day Avg'}
                    ],
                'layout':{
                    'title':input_data
                },
            },
            style = 
            {
                'border':f'2px {color} solid'
            }
        )
    
    except Exception as e:
        graph = html.Div("Error retrieving stock data.")

    return graph

if __name__ == '__main__':
    app.run_server()