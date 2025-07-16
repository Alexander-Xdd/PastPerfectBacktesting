import pandas as pd

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

class PastPerfectBacktesting:
    def __init__(self, file, take_profit, stop_loss,
                 dep = 0.0, transaction_fee = 0.0, fetch_data_start_row = 100, limit = 100,
                 display_intermediate_data = False, cooldown = 0):
        self.hdf = PastPerfectBacktesting.get_dataset(file[0], file[1])

        self.tp = take_profit / 100
        self.sl = stop_loss / 100
        self.dep = dep
        self.start_deposit = dep
        self.transaction_fee = transaction_fee / 100
        self.fetch_data_start_row = fetch_data_start_row
        self.limit = limit
        self.display_intermediate_data = display_intermediate_data
        self.cooldown = cooldown

        self.last_signal = None
        self.query_number = 0
        self.profit = 1
        self.lose = 1


    @staticmethod
    def get_dataset(name, options):
        df = pd.read_csv(name)

        options = {"open": "open", "high": "high", "low": "low",
                   "close": "close", "volume": "volume", "reversed": False} | options
        if options["open"]:
            df = df.iloc[::-1].reset_index(drop=True)
        df = df.rename(columns={
            options["open"]: 'open',
            options["high"]: 'high',
            options["low"]: 'low',
            options["close"]: 'close',
            options["volume"]: 'volume',
        })

        return df[['open', 'high', 'low', 'close', 'volume']].astype(float)

    def ema(self, ema_fast=9, ema_slow=21):
        """ EMA (Exponential Moving Average). Adds 'ema_fast', 'ema_slow' """

        self.hdf['ema_fast'] = EMAIndicator(self.hdf['close'], window=ema_fast).ema_indicator()
        self.hdf['ema_slow'] = EMAIndicator(self.hdf['close'], window=ema_slow).ema_indicator()
        return self

    def rsi(self, rsi_period=14):
        """ RSI (Relative Strength Index). Adds 'rsi' """

        self.hdf['rsi'] = RSIIndicator(self.hdf['close'], window=rsi_period).rsi()
        return self

    def fetch_data(self):
        while True:
            if self.fetch_data_start_row + self.query_number + self.limit > len(self.hdf):
                break
            df = self.hdf[self.fetch_data_start_row + self.query_number:
                 self.fetch_data_start_row + self.query_number + self.limit].reset_index(drop=True).copy()
            self.query_number += 1
            yield df


    @staticmethod
    def generate_signal(df):
        current = df.iloc[-1]
        previous = df.iloc[-2]

        if (previous['ema_fast'] <= previous['ema_slow']) and (current['ema_fast'] > current['ema_slow']):
            return 'BUY', current['close']

        elif (previous['ema_fast'] >= previous['ema_slow']) and (current['ema_fast'] < current['ema_slow']):
            return 'SELL', current['close']

        return None


    def calculate_orders(self, order_history, price):
        for order in order_history:
            if order["signal_type"] == 'BUY':
                if price >= order["take_profit"]:
                    self.profit += 1
                    self.dep += (price - (price * self.transaction_fee))
                    order_history.remove(order)
                if price <= order["stop_loss"]:
                    self.lose += 1
                    self.dep += (price - (price * self.transaction_fee))
                    order_history.remove(order)
            else:
                dep_price = order["entry_price"] + (order["entry_price"] - price)
                if price <= order["take_profit"]:
                    self.profit += 1
                    self.dep += (dep_price - (dep_price * self.transaction_fee))
                    order_history.remove(order)
                if price >= order["stop_loss"]:
                    self.lose += 1
                    self.dep += (dep_price - (dep_price * self.transaction_fee))
                    order_history.remove(order)


    def backtesting(self, generate_signal = generate_signal):
        order_history = []
        cd = 0
        print("Testing...")

        for df in self.fetch_data():
            signal = generate_signal(df)
            self.calculate_orders(order_history, float(df['close'].iloc[-1]))

            if self.display_intermediate_data:
                print(f"-" * 50)
                print(f"Backtested bars: {self.query_number}")
                print(f"Orders: {order_history}")
                print(f"Deposit: {self.dep}")
                print(f"The ratio of profitable/unprofitable transactions: {self.profit}/{self.lose}")
                print(f"Algorithm efficiency: {(self.profit) / ((self.profit) + (self.lose)) * 100:.2f}%")
                print(f"Efficiency of the algorithm considering tp/pl: {(self.profit * self.tp) /
                                                                        ((self.profit * self.tp) + (self.lose * self.sl)) *
                                                                        100:.2f}%")

            if cd != 0:
                cd -= 1
                continue

            if signal:
                cd = self.cooldown
                signal_type, entry_price = signal
                price = float(entry_price)
                price = price - (price * self.transaction_fee)
                if signal_type == 'BUY':
                    order_history.append({"signal_type": signal_type, "entry_price": price,
                                          "take_profit": price + price*self.tp,
                                          "stop_loss": price - price*self.sl})
                    self.dep -= price
                else:
                    order_history.append({"signal_type": signal_type, "entry_price": price,
                                          "take_profit": price - price*self.tp,
                                          "stop_loss": price + price*self.sl})
                    self.dep -= price


        self.dep += sum([order["entry_price"] for order in order_history])
        print(f"=" * 50)
        print(f"\nBacktested bars: {self.query_number}")
        print(f"Сhanging the deposit: {self.start_deposit} -> {self.dep}")
        print(f"The ratio of profitable/unprofitable transactions: {self.profit}/{self.lose}")
        print(f"Algorithm efficiency: {(self.profit) / ((self.profit) + (self.lose)) * 100:.2f}%")
        print(f"Efficiency of the algorithm considering tp/pl: {(self.profit * self.tp) /
                                                                ((self.profit * self.tp) + (self.lose * self.sl)) *
                                                                100:.2f}%")