import streamlit as st
import pandas as pd
import base64
import matplotlib.pyplot as plt
import requests
import json
from PIL import Image
from bs4 import BeautifulSoup


# Page expands to full width
st.set_page_config(layout='wide')

image =  Image.open('images/crypto-logo.jpg')

st.image(image, width=500)

st.title('Crypto Price App')
st.markdown(''' 
This app retrieves cryptocurrency prices for the top 100 cryptocurrency from **CoinMarketApp**
''')

# About
expander_bar = st.beta_expander('About')
expander_bar.markdown('''
* **Python libraries:** base64, streamlit, BeautifulSoup
* **Data source:** [CoinMarketCap](http://coinmarketcap.com)
* **Credit:** Web scraper adapted from the Medium article *[Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* written by [Bryan Feng](https://medium.com/@bryanf)
''')

# Divide page to 3 columns
col1 = st.sidebar
col2, col3 = st.beta_columns((2, 1))

# Sidebar
col1.header('Input Options')

currency_price_unit = col1.selectbox('Select currency for price', ('USD', 'BTC', 'ETH'))

# Web scraping of CoinMarketCap data
@st.cache
def load_data():
    cmc = requests.get('http://coinmarketcap.com')
    soup = BeautifulSoup(cmc.content, 'html.parser')

    data = soup.find('script', id='__NEXT_DATA__', type='application/json')

    coins = {}
    coin_data = json.loads(data.contents[0])
    listings = coin_data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    for i in listings:
        coins[str(i['id'])] = i['slug']

    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []

    for i in listings:
        coin_name.append(i['slug'])
        coin_symbol.append(i['symbol'])
        price.append(i['quote'][currency_price_unit]['price'])
        percent_change_1h.append(i['quote'][currency_price_unit]['percentChange1h'])
        percent_change_24h.append(i['quote'][currency_price_unit]['percentChange24h'])
        percent_change_7d.append(i['quote'][currency_price_unit]['percentChange7d'])
        market_cap.append(i['quote'][currency_price_unit]['marketCap'])
        volume_24h.append(i['quote'][currency_price_unit]['volume24h'])

    df = pd.DataFrame(columns=['coin_name', 'coin_symbol', 'market_cap', 'change_1h', 'change_24h', 'change_7d', 'price', 'volume_24h'])
    df['coin_name'] = coin_name
    df['coin_symbol'] = coin_symbol
    df['price'] = price
    df['change_1h'] = percent_change_1h
    df['change_24h'] = percent_change_24h
    df['change_7d'] = percent_change_7d
    df['market_cap'] = market_cap
    df['volume_24h'] = volume_24h
    
    return df


df = load_data()

# Sidebar - crypto selection
coins = sorted(df['coin_symbol'])
selected_coin = col1.multiselect('Cryptocurrency', coins, coins)
df_selected_coin = df[(df['coin_symbol'].isin(selected_coin))]

# Sidebar - number of coins
num_coin = col1.slider('Display top N coins', 1, 100, 100)
df_coins = df_selected_coin[:num_coin]

# Sidebar - percent change timeframe
change_timeframe = col1.selectbox('Percent change timeframe', ['7d', '24h', '1h'])
change_dict = {'7d':'change_7d', '24h':'change_24h', '1h':'change_1h'}
selected_change = change_dict[change_timeframe]

# Sidebar - sort values
sort_values = col1.selectbox('Sort values?', ['Yes', 'No'])


col2.subheader('Price Data of Selected Cryptocurrencies')
col2.write('Data Dimension: ' + str(df_selected_coin.shape[0]) + ' rows and ' + str(df_selected_coin.shape[1]) + ' columns.')
col2.dataframe(df_coins)

# Downlaod csv
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" downlaod="crypto.csv">Download CSV</a>'
    return href

col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)


# Prepare data for bar plot
col2.subheader('Table of % price change')
df_change = pd.concat([df_coins.coin_symbol, df_coins.change_1h, df_coins.change_24h, df_coins.change_7d], axis=1)
df_change = df_change.set_index('coin_symbol')
df_change['positive_change_1h'] = df_change['change_1h'] > 0
df_change['positive_change_24h'] = df_change['change_24h'] > 0
df_change['positive_change_7d'] = df_change['change_7d'] > 0

col2.dataframe(df_change)

# Creating bar plot
col3.subheader('Bar plot of % price change')

if change_timeframe == '7d':

    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['change_7d'])

    col3.write('*7 day period*')

    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['change_7d'].plot(kind='barh', color=df_change.positive_change_7d.map({True:'g', False:'r'}))
    col3.pyplot(plt)
elif change_timeframe == '24h':

    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['change_24h'])

    col3.write('*24 hour period*')

    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['change_24h'].plot(kind='barh', color=df_change.positive_change_24h.map({True:'g', False:'r'}))
    col3.pyplot(plt)
else:

    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['change_1h'])

    col3.write('*1 hour period*')

    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['change_1h'].plot(kind='barh', color=df_change.positive_change_1h.map({True:'g', False:'r'}))
    col3.pyplot(plt)