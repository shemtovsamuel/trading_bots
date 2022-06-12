#!/usr/bin/python3
# -*- coding: iso-8859-1 -*
""" Python starter bot for the Crypto Trader games, from ex-Riddles.io """
__version__ = "1.0"

import math
import sys
from datetime import datetime

tab_sd = []

class Bot:
    def __init__(self):
        self.botState = BotState()
        self.count_buy = 0
        self.count_sell = 0

    def run(self):
        while True:
            reading = input()
            if len(reading) == 0:
                continue
            self.parse(reading)

    def calculate_rsi(self, period):
        candle = self.botState.candle
        loss = 0
        gain = 0
        for i in range (period, 0, -1):
            diff = abs(self.botState.charts["USDT_BTC"].closes[candle - i] - self.botState.charts["USDT_BTC"].closes[candle - i - 1])
            if (self.botState.charts["USDT_BTC"].closes[candle - i] < self.botState.charts["USDT_BTC"].closes[candle - i - 1]):
                loss += diff
            if (self.botState.charts["USDT_BTC"].closes[candle - i] > self.botState.charts["USDT_BTC"].closes[candle - i - 1]):
                gain += diff
        avg_gain = gain / period
        avg_loss = loss / period
        rs = avg_gain / avg_loss
        rsi = 100 - (100/(1 + rs))
        return round(rsi)

    def calculate_sma(self, period):
        sma = 0
        candles = 0
        nb_candle = self.botState.candle
        for i in range (period, 0, -1):
            candles += round(self.botState.charts["USDT_BTC"].closes[nb_candle - i])
        sma = candles / period
        return sma

    def calculate_standard_deviation(self, period):
        sd = 0
        x = 0
        y = 0
        candle = self.botState.candle
        for i in range (candle,  candle - period, -1):
            x += abs(self.botState.charts["USDT_BTC"].opens[candle - i] - self.botState.charts["USDT_BTC"].closes[candle - i]) / 2
            y += pow(abs(self.botState.charts["USDT_BTC"].opens[candle - i] - self.botState.charts["USDT_BTC"].closes[candle - i]) / 2, 2)
        sd = math.sqrt(y / candle - pow(x / candle, 2))
        return sd

    def parse(self, info: str):
        tmp = info.split(" ")
        if tmp[0] == "settings":
            self.botState.update_settings(tmp[1], tmp[2])
        if tmp[0] == "update":
            if tmp[1] == "game":
                self.botState.update_game(tmp[2], tmp[3])
        if tmp[0] == "action":
            value = 10
            dollars = self.botState.stacks["USDT"]
            btc = self.botState.stacks["BTC"]
            current_closing_price = self.botState.charts["USDT_BTC"].closes[-1]
            affordable = dollars / current_closing_price
            rsi = self.calculate_rsi(10)
            standart_deviation = self.calculate_standard_deviation(10)
            tab_sd.append(round(standart_deviation, 2))
            sma = self.calculate_sma(10)
            ub = sma + (2 * standart_deviation)
            lb = sma - (2 * standart_deviation)
            buy = value / current_closing_price
            sell = (buy * current_closing_price) / current_closing_price
            if  btc > (sell * (1 + (self.botState.nb_green / 20))) and ub >= (current_closing_price * 0.95) and rsi > 60:
                self.botState.nb_green += 1
                self.botState.nb_red = 0
                print(f'sell USDT_BTC {sell * (1 + (self.botState.nb_green / 20))}', flush=True)
                self.count_sell += 1
            elif affordable >= (buy * (1 + (self.botState.nb_red / 20))) and lb <= (current_closing_price * 1.05) and rsi < 30:
                self.botState.nb_red += 1
                self.botState.nb_green = 0
                print(f'buy USDT_BTC {buy * (1 + (self.botState.nb_red / 20))}', flush=True)
                self.count_buy += 1
            else:
                print(f'no_moves', flush=True)
class Candle:
    def __init__(self, format, intel):
        tmp = intel.split(",")
        for (i, key) in enumerate(format):
            value = tmp[i]
            if key == "pair":
                self.pair = value
            if key == "date":
                self.date = int(value)
            if key == "high":
                self.high = float(value)
            if key == "low":
                self.low = float(value)
            if key == "open":
                self.open = float(value)
            if key == "close":
                self.close = float(value)
            if key == "volume":
                self.volume = float(value)

    def __repr__(self):
        return str(self.pair) + str(self.date) + str(self.close) + str(self.volume)

class Chart:
    def __init__(self):
        self.dates = []
        self.opens = []
        self.highs = []
        self.lows = []
        self.closes = []
        self.volumes = []
        self.indicators = {}

    def add_candle(self, candle: Candle):
        self.dates.append(candle.date)
        self.opens.append(candle.open)
        self.highs.append(candle.high)
        self.lows.append(candle.low)
        self.closes.append(candle.close)
        self.volumes.append(candle.volume)

class BotState:
    def __init__(self):
        self.timeBank = 0
        self.maxTimeBank = 0
        self.timePerMove = 1
        self.candleInterval = 1
        self.candleFormat = []
        self.candlesTotal = 0
        self.candlesGiven = 0
        self.initialStack = 0
        self.transactionFee = 0.1
        self.date = 0
        self.stacks = dict()
        self.charts = dict()
        self.candle = 0
        self.nb_red = 0
        self.nb_green = 0

    def update_chart(self, pair: str, new_candle_str: str):
        if not (pair in self.charts):
            self.charts[pair] = Chart()
        new_candle_obj = Candle(self.candleFormat, new_candle_str)
        self.charts[pair].add_candle(new_candle_obj)

    def update_stack(self, key: str, value: float):
        self.stacks[key] = value

    def update_settings(self, key: str, value: str):
        if key == "timebank":
            self.maxTimeBank = int(value)
            self.timeBank = int(value)
        if key == "time_per_move":
            self.timePerMove = int(value)
        if key == "candle_interval":
            self.candleInterval = int(value)
        if key == "candle_format":
            self.candleFormat = value.split(",")
        if key == "candles_total":
            self.candlesTotal = int(value)
        if key == "candles_given":
            self.candlesGiven = int(value)
        if key == "initial_stack":
            self.initialStack = int(value)
        if key == "transaction_fee_percent":
            self.transactionFee = float(value)

    def update_game(self, key: str, value: str):
        if key == "next_candles":
            self.candle += 1
            new_candles = value.split(";")
            self.date = int(new_candles[0].split(",")[1])
            for candle_str in new_candles:
                candle_infos = candle_str.strip().split(",")
                self.update_chart(candle_infos[0], candle_str)
        if key == "stacks":
            new_stacks = value.split(",")
            for stack_str in new_stacks:
                stack_infos = stack_str.strip().split(":")
                self.update_stack(stack_infos[0], float(stack_infos[1]))

if __name__ == "__main__":
    mybot = Bot()
    mybot.run()
