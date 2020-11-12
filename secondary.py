#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Binance Interview """

import sys
import argparse
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
    required=False,
)
args = parser.parse_args()


def filter_exchange_info(exchange_info, filter_key, filter_value):
    # TODO: make this work for multiple filters and multiple sub-values such as:
    # 'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
    """ Filter exchange_info by sub-attribute
    :returns: list - List of product dictionaries

    .. code-block:: python
    :raises: BinanceRequestException, BinanceAPIException

    """
    # Symbols list
    symbol_list = []
    for symbol in exchange_info['symbols']:
        if filter_value in symbol.get(filter_key):
            symbol_list.append(symbol["symbol"])
    return symbol_list


def main():
    """  Main Function """
    # Initialize Client binance object
    client = Client(api_key=args.apikey, api_secret=args.secret)

    # Get current exchangeInfo as Dict
    exchange = client.get_exchange_info()

    # Get List of symbols filtered by quoteAsset
    # TODO: Make the filter_key part of argparse params, don't hard-code, make args more generic overall
    filtered_symbols = filter_exchange_info(exchange_info=exchange, filter_key="quoteAsset", filter_value=args.quoteAsset)

    # Exit success
    sys.exit(0)


# Execute main function
main()
