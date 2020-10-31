#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Binance Interview """

import concurrent.futures
import sys
import argparse
import requests
import simplejson
# TODO: Use the community binance python lib
# from binance.client import Client
#parser.add_argument(
#    "-k",
#    "--apikey",
#    type=str,
#    help="A valid API token for querying the Binance SPOT API",
#    required=False,
#)
#parser.add_argument(
#    "-s",
#    "--secret",
#    type=str,
#    help="A valid API secret token for querying the Binance SPOT API",
#    required=False,
#)

# Parse Arguments
parser = argparse.ArgumentParser(
    description=" Binance Interview Questions Script ", )

parser.add_argument(
    "-q",
    "--quoteAsset",
    type=str,
    help=
    "A quote asset type to filter symbols by in the Binance SPOT API (BTC,USDT,etc)",
    required=False,
)
args = parser.parse_args()


def make_request(url):
    """  Hit a URL and return a requests object iff the return code was 200 OK """
    # TODO: Handle all error codes returned by Binance as documented in
    # https://github.com/binance-exchange/binance-official-api-docs/blob/master/errors.md
    try:
        request = requests.get(url)
        if request.status_code != 200:
            sys.exit("Request to " + url + " endpoint returned HTTP code " +
                     str(request.status_code))
        return request
    # FIXME: This does not catch all possible exceptions, such as Host not found or URL invalid
    except requests.ConnectionError as err:
        # GET request to GET https://api.binance.com/api/v3/ping
        sys.exit("Could not connect to API endpoint! " + err +
                 "Please check your connection.")


def get_response_as_json(request_obj):
    """ Return JSON-formatted string from passed request object """
    try:
        return request_obj.json()
    except simplejson.errors.JSONDecodeError as err:
        # TODO: Make this output more useful.  "Expecting value: line 1 column 1 (char 0)" isn't all that helpful.
        # TODO: Handle exceptions in addition to JSONDecodeError
        sys.exit(err)


def get_kline(api_url, symbol, interval="1d"):
    """ Return List of klines for a passed symbol and interval (default to 24h) """
    # FIXME: I don't like swapping between List and JSON here, can we stick to JSON?
    kline = make_request(api_url + "klines" + "?symbol=" + symbol +
                         "&interval=" + interval)
    return list(kline.json())


def sort_klines_by_volume(kline_list_obj):
    """ Sort kline List of Lists object by Volume in sub-Lists """
    # TODO: Make a struct or something to sort by an arbitrary value in klines List instead of hard-coding the 7th element here
    return sorted(kline_list_obj, key=lambda x: x[6])


def find_symbols_by_quote_asset(exchange_json_obj, quote_asset_type=None):
    """ Filter symbols by quoteAsset, return List (all symbols if not specified) """
    symbol_list = []
    for item in exchange_json_obj.get("symbols"):
        if quote_asset_type in item.get("quoteAsset"):
            symbol_list += [item.get("symbol")]
    return symbol_list


def main():
    """ Main Function """

    # Set base API URL
    api_url = "https://api.binance.com/api/v3/"

    # Basic connectivity check
    make_request(api_url + "ping")

    # Get exchangeInfo as JSON
    exchange = get_response_as_json(make_request(api_url + "exchangeInfo"))

    # Populate symbols list by searching through exchangeInfo for quoteAssets of type args.quoteAsset
    symbol_list = find_symbols_by_quote_asset(exchange, args.quoteAsset)

    # Make a dictionary with the keys being symbols and values being empty
    # Lists (which will be populated below as Lists of Lists by getting the
    # klines for each symbol)
    symbol_dict = {}
    for item in symbol_list:
        symbol_dict.__setitem__(item, [])

    # ThreadPool the API calls for getting klines.
    # TODO: Make this ThreadPooling a function, maybe don't hard-code workers number?
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []  # Empty List to track Future objects
        for key in symbol_dict:
            futures.append(
                executor.submit(get_kline,
                                api_url=api_url,
                                symbol=key,
                                interval="1d"))
        for future in concurrent.futures.as_completed(futures):
            # Populate the dictionary of symbols (keys) with the top value returned for the klines over the last 24h for that symbol
            for key in symbol_dict:
                symbol_dict[key] = sort_klines_by_volume(future.result())[0]

    # Sort the Dict by 7th element in List item (Volume), return sorted List
    sorted_symbols = sorted(symbol_dict.items(),
                            key=lambda x: x[1][6],
                            reverse=True)

    # Print the first 5 items in the sorted List
    print("Top 5 symbols by Volume over the last 24h")
    for item in sorted_symbols[0:5]:
        print(item[0])


# Execute main function
main()
