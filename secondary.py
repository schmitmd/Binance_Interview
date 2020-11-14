#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Binance Interview """

import argparse
import datetime
import time
import sys
import concurrent.futures
from binance.client import Client

# Initialize CLI arguments
parser = argparse.ArgumentParser(description='Binance Interview')
parser.add_argument(
    "-k",
    "--apikey",
    type=str,
    help="A valid API token for querying the Binance SPOT API",
    required=False,
)
parser.add_argument(
    "-s",
    "--secret",
    type=str,
    help="A valid API secret token for querying the Binance SPOT API",
    required=False,
)
parser.add_argument(
    "-q",
    "--quoteAsset",
    type=str,
    help=
    "A quote asset type to filter symbols by in the Binance SPOT API (BTC,USDT,etc)",
    required=True, # TODO: This shouldn't be a required arg. Set sane defaults
)
args = parser.parse_args()


def filter_exchange_info(exchange_info, filter_key, filter_value):
    # TODO: make this work for multiple filters and multiple sub-values such as:
    # 'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
    """ Filter exchange_info by sub-attribute
    :param exchange_info: required
    :type exchange_info: dict
    :param filter_key: required
    :type filter_key: str
    :param filter_value: required
    :type filter_value: str

    :returns: list - List of symbols
    """
    # Symbols list
    symbol_list = []
    for symbol in exchange_info['symbols']:
        if filter_value in symbol.get(filter_key):
            symbol_list.append(symbol["symbol"])
    return symbol_list


def threaded_get_klines(binance_client, symbol_dict, start_ms, end_ms):
    """ Use a ThreadPool to get klines faster
    :param binance_client: required
    :type binance_client: binance.client.Client
    :param symbol_dict: required
    :type symbol_dict: dict
    :param start_ms: required
    :type start_ms: int
    :param end_ms: required
    :type end_ms: int

    :returns: Dict with symbol keys and kline result (List) values
    """
    # Empty Dict to return when we're done
    temp_symbol_dict = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = { executor.submit(
            binance_client.get_klines, symbol=key,
            interval=Client.KLINE_INTERVAL_30MINUTE, startTime=start_ms, endTime=end_ms): key
            for key in symbol_dict
            }

        for future in concurrent.futures.as_completed(futures):
            # Only add if something was returned
            if future.result():
                temp_symbol_dict[futures[future]] = future.result()
    return temp_symbol_dict


def main():
    """  Main Function """
    # Initialize Client binance object
    client = Client(api_key=args.apikey, api_secret=args.secret)

    # Get current time and 24 hours ago in milliseconds
    now_ms = round(time.time_ns()/1000000)
    day_ago_ms = now_ms - 86400000

    # Get current exchangeInfo as Dict
    exchange = client.get_exchange_info()

    # Make a Dict of symbols filtered by quoteAsset, to be populated with klines
    # TODO: Make the filter_key part of argparse params, don't hard-code, make args more generic overall
    kline_dict = dict.fromkeys(filter_exchange_info(exchange_info=exchange, filter_key="quoteAsset", filter_value=args.quoteAsset), [])

    # Populate klines in the Dict
    kline_dict = threaded_get_klines(binance_client=client, symbol_dict=kline_dict, start_ms=day_ago_ms, end_ms=now_ms)


# Execute main function
main()
