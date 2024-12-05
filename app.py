import numpy as np
import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from contrans import contrans
import plotly.figure_factory as ff

ct = contrans()
server, engine = ct.connect_to_postgres(ct.POSTGRES_PASSWORD, host='postgres')


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

dropdown_options_cat = [{'label':'Hotels','value':'hotels'},{'label':'Attractions','value':'attractions'},{'label':'Restaurants','value':'restaurants'}]

dropdown_options_star = [{'label':'1 Star','value':1},{'label':'2 Star','value':2},{'label':'3 Star','value':3},{'label':'4 Star','value':4},{'label':'5 Star','value':5}]

dropdown_options_price = [{'label':'$','value':'$'},{'label':'$$','value':'$$'},{'label':'$$$','value':'$$$'},{'label':'$$$$','value':'$$$$'}]

dropdown_option_review_filter = [{'label':'1 Star','value':1.0},{'label':'2 Star','value':2.0},{'label':'3 Star','value':3.0},{'label':'4 Star','value':4.0},{'label':'5 Star','value':5.0}]

dropdown_options_biz = []

app.layout = html.Div([
    html.H1("Travel Plan Dataset", style={'text-align': 'center'}),
    html.Div([
        dcc.Markdown('Select the categories here:'),
        dcc.Dropdown(id='dropdown_cat', options=dropdown_options_cat, placeholder="Select the category...", value='hotels'),

        dcc.Markdown('Select the stars here:'),
        dcc.Dropdown(id='dropdown_star', options=dropdown_options_star, placeholder="Select the rating...", value=4),

        dcc.Markdown('Select the price range here:'),
        dcc.Dropdown(id='dropdown_price', options=dropdown_options_price, placeholder="Select the price range...", value='$$'),

        dcc.Markdown('Select the business here:'),
        dcc.Dropdown(id='dropdown_biz', options=dropdown_options_biz, placeholder="Select the business...", value='')

        ], style={'width': '25%', 'float': 'left'}),
    html.Div([
        dcc.Tabs([
            dcc.Tab(label='Basic Info', children=[
                html.Div(id='basic-info-tab', style={'backgroundColor': '#f2f2f2', 'padding': '50px', 'border': '1px solid #ccc'})
            ]),
            dcc.Tab(label='Extracted Info', children=[
                html.Div(id='extracted-info-tab', style={'backgroundColor': '#f2f2f2', 'padding': '50px', 'border': '1px solid #ccc'})
            ]),
            dcc.Tab(label='Related Reviews', children=[
                html.Div(id='related-reviews-content', style={'height': '500px', 'overflow-y': 'auto', 'backgroundColor': '#f2f2f2', 'padding': '50px', 'border': '1px solid #ccc'},children=[
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between'},
                     children=[
                        html.H1('Related Reviews'),
                        dcc.Dropdown(id='dropdown_review_filter', options=dropdown_option_review_filter, placeholder="Select rating", value='',style={'width': '200px'})
                     ])
                ])
            ])
        ])
    ], style={'width':'72%', 'float': 'right'}),    
])



@app.callback([Output(component_id = 'dropdown_biz', component_property = 'options')],
             [Input(component_id = 'dropdown_cat', component_property = 'value'),
              Input(component_id = 'dropdown_star', component_property = 'value'),
              Input(component_id = 'dropdown_price', component_property = 'value')])

def getBiz(cat,star,price):
    query = f'''
    SELECT business_id, name, address
    FROM {cat}
    '''
    if(star != None and price == None):
        query += f' WHERE stars >= {star}'
    if(price != None and star == None):
        query += f' WHERE price = "{price}"'
    if(price != None and star != None):
        query += f" WHERE stars >= {star} AND price = '{price}'"
    df = pd.read_sql_query(query, con=engine)
    options = [{'label': row['name'], 'value': row['business_id']} for index, row in df.iterrows()]
    return [options]


# Define the callback function
@app.callback(
    Output('basic-info-tab', 'children'),
    [Input('dropdown_cat', 'value'),
     Input('dropdown_biz', 'value')]
)
def update_basic_info_tab(cat,biz):
    # Define the SQL query
    query = f'''
    SELECT name, address, stars, price
    FROM {cat} WHERE business_id = '{biz}'
    '''

    # Read the data from the database
    df = pd.read_sql_query(query, con = engine)

    # Create the tab content
    tab_content = [
        html.H1('Basic Info'),
        html.P(f'Name: {df["name"][0]}'),
        html.P(f'Address: {df["address"][0]}'),
        html.P(f'Stars: {df["stars"][0]}'),
        html.P(f'Price: {df["price"][0]}')
    ]

    # Return the tab content
    return tab_content

@app.callback(
    Output('extracted-info-tab', 'children'),
    [Input('dropdown_cat', 'value'),
     Input('dropdown_biz', 'value')]
)
def update_extracted_info_tab(cat,biz):
    # Define the SQL query
    if (cat == 'hotels'):
        query = f'''
        SELECT name,quality, location, service, safety
        FROM {cat} WHERE business_id = '{biz}'
        '''
        # Read the data from the database
        df = pd.read_sql_query(query, con = engine)

        # Create the tab content
        tab_content = [
            html.H1('Extracted Info'),
            html.P(f'Name: {df["name"][0]}'),
            html.P(f'quality: {df["quality"][0]}'),
            html.P(f'location: {df["location"][0]}'),
            html.P(f'service: {df["service"][0]}'),
            html.P(f'safety: {df["safety"][0]}')
        ]

    # Return the tab content
    return tab_content

@app.callback(
    Output('related-reviews-content', 'children'),
    [Input('dropdown_cat', 'value'),
     Input('dropdown_biz', 'value'),
     Input('dropdown_review_filter', 'value')]
)
def update_related_reviews_tab(cat, biz,rating):
    if(cat == 'hotels'):
        query = f'''
        SELECT text,stars
        FROM hotels_reviews
        WHERE business_id = '{biz}'
        '''

        if(rating != None):
            query += f' AND stars = {rating}'

        df = pd.read_sql_query(query, con=engine)
        tab_content = [
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between'},
                     children=[
                        html.H1('Related Reviews'),
                        dcc.Dropdown(id='dropdown_review_filter', options=dropdown_option_review_filter, placeholder="Select rating", value='',style={'width': '200px'})
                     ]),
            html.Ul([
                html.Li(f"{stars}/5 - {review_text}") for stars,review_text in zip(df['stars'],df['text'])
            ])
        ]
        return tab_content

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)