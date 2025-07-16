PastPerfectBacktesting
======================
PastPerfectBacktesting a flexible and convenient tool for testing trading strategies based on historical data. The project allows you to evaluate the effectiveness of strategies, analyze risks and optimize parameters before launching in real conditions.

Installation
-----------
```bash
git clone https://github.com/Alexander-Xdd/PastPerfectBacktesting.git
```
```bash
pip install pandas ta
```

Output format
-------------
When display_intermediate_data=False

<img width="456" height="112" alt="image" src="https://github.com/user-attachments/assets/5441dd51-d52b-4685-8286-e9f87c376a2c" />

When display_intermediate_data=True, information is displayed after each bar.

Beginning
-----------
```python
from PastPerfectBacktesting.ppbt import PastPerfectBacktesting

ppbt = PastPerfectBacktesting(
    file = [r'C:\btc_dataset\BTC-Daily.csv', {"volume": "Volume BTC", "reversed": True}],
    take_profit = 0.9,  # %, Allows the bidder to close the position on time and make the profit he expected.
    stop_loss = 0.3,  # %, A stop-loss prevents a bidder from losing more money than he is willing to.
    dep = 0.0, # The initial deposit, can be ignored.
    transaction_fee = 0.055, # %, Trading commissions - taker, maker, depending on the exchange
    fetch_data_start_row = 100, # The initial rows will not have indicators, it depends on which indicators to use.
    limit = 100, # The limit of the rows that will be extracted for the analysis, depends on which signals source
    display_intermediate_data = False,
    cooldown = 5 # bars, Ignores this number of bars before opening the next position.
)

ppbt.rsi().ema()
ppbt.backtesting()
```
You need to download the asset's csv dataset with the columns 'open', 'high', 'low', 'close', 'volume', for example from kaggle.com. If the column names are different, then rename.
For example, for the file "BTC.csv" with the columns 'unix', 'date', 'symbol', 'Open', 'high', 'low', 'close', 'Volume BTC', 'Volume USD', located in "C:\datasets".
```python
    file = [r'C:\datasets\BTC.csv', {"open": "Open", "volume": "Volume BTC"}],
```
'high', 'low', 'close' are written correctly, the other columns are not used. The "reversed": True flag should be set only if the lines go from new to old.

Indicators
----------
For example, you can call these methods to calculate indicators. Columns 'ema_fast', 'ema_slow', 'rsi' will be added.
```python
ppbt.ema().rsi()
```
For custom indicators, write a function using the "ta" library. An example of such a function
```python
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
def calculate_my_indicators(df, ema_fast=9, ema_slow=21, rsi_period=14, atr_period=14):
    # EMA
    df['ema_fast'] = EMAIndicator(df['close'], window=ema_fast).ema_indicator()
    df['ema_slow'] = EMAIndicator(df['close'], window=ema_slow).ema_indicator()

    # RSI
    df['rsi'] = RSIIndicator(df['close'], window=rsi_period).rsi()

    # ATR
    df['atr'] = AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=atr_period
    ).average_true_range()
    return df

ppbt.hdf = calculate_my_indicators(ppbt.hdf, ema_fast=9, ema_slow=21, rsi_period=14)
```

Signals
----------
After calculating the indicators, it's time to receive the signals. The function may look like this
```python
def generate_signal_ema(df):
    current = df.iloc[-1]
    previous = df.iloc[-2]

    # Buy signal: the fast EMA crosses the slow one from bottom to top
    if (previous['ema_fast'] <= previous['ema_slow']) and (current['ema_fast'] > current['ema_slow']):
        return 'BUY', current['close']

    # Sell signal: Fast EMA crosses slow one from top to bottom
    elif (previous['ema_fast'] >= previous['ema_slow']) and (current['ema_fast'] < current['ema_slow']):
        return 'SELL', current['close']

    # There is no signal
    return None
ppbt.backtesting(generate_signal_ema)
```
Or like this :)
```python
import random
def generate_random_signal(df):
    current = df.iloc[-1]
    r = random.randint(0, 1)

    if r:
        return 'BUY', current['close']

    else:
        return 'SELL', current['close']
ppbt.backtesting(generate_signal_ema)
```

Example of the full code
----------
```python
from PastPerfectBacktesting.ppbt import PastPerfectBacktesting

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

ppbt = PastPerfectBacktesting(
    file = [r'C:\btc_dataset\BTC-Daily.csv', {"volume": "Volume BTC", "reversed": True}],
    take_profit = 0.9,  # %, Allows the bidder to close the position on time and make the profit he expected.
    stop_loss = 0.3,  # %, A stop-loss prevents a bidder from losing more money than he is willing to.
    dep = 0.0, # The initial deposit, can be ignored.
    transaction_fee = 0.055, # %, Trading commissions - taker, maker, depending on the exchange
    fetch_data_start_row = 100, # The initial rows will not have indicators, it depends on which indicators to use.
    limit = 100, # The limit of the rows that will be extracted for the analysis, depends on which signals source
    display_intermediate_data = False,
    cooldown = 5 # bars, Ignores this number of bars before opening the next position.
)

def calculate_my_indicators(df, ema_fast=9, ema_slow=21, rsi_period=14, atr_period=14):
    # EMA
    df['ema_fast'] = EMAIndicator(df['close'], window=ema_fast).ema_indicator()
    df['ema_slow'] = EMAIndicator(df['close'], window=ema_slow).ema_indicator()

    # RSI
    df['rsi'] = RSIIndicator(df['close'], window=rsi_period).rsi()

    # ATR
    df['atr'] = AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=atr_period
    ).average_true_range()
    return df

ppbt.hdf = calculate_my_indicators(ppbt.hdf, ema_fast=9, ema_slow=21, rsi_period=14)

def generate_signal_ema(df):
    current = df.iloc[-1]
    previous = df.iloc[-2]

    # Buy signal: the fast EMA crosses the slow one from bottom to top
    if (previous['ema_fast'] <= previous['ema_slow']) and (current['ema_fast'] > current['ema_slow']):
        return 'BUY', current['close']

    # Sell signal: Fast EMA crosses slow one from top to bottom
    elif (previous['ema_fast'] >= previous['ema_slow']) and (current['ema_fast'] < current['ema_slow']):
        return 'SELL', current['close']

    # There is no signal
    return None

ppbt.backtesting(generate_signal_ema)
```
