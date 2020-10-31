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
parser.add_argument(
    "-n",
    "--notional",
    type=int,
    help="Number of top bids and asks to get notional values for by symbol",
    required=False,
)
args = parser.parse_args()


def make_request(url):
    """  Hit a URL and return a requests object if the return code was 200 OK """
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
    kline = make_request(api_url + "klines" + "?symbol=" + symbol +
                         "&interval=" + interval)
    return list(kline.json())


def get_order_book_request_limit(limit):
    """ Return a valid request limit parameter (int) for the order book API endpoint """
    valid_limits = [5, 10, 20, 50, 100, 500, 1000, 5000]
    for value in valid_limits:
        if limit <= value:
            return value
    sys.exit("The maximum number of top bids/asks you can request is " +
             str(valid_limits[-1]))


def sort_klines_by_volume(kline_list_obj):
    """ Sort kline List of Lists object by Volume in sub-Lists """
    # TODO: Make a struct or something to sort by an arbitrary value in klines List instead of hard-coding the 7th element here
    return sorted(kline_list_obj, key=lambda x: x[6])


def find_symbols_by_quote_asset(exchange_json_obj, quote_asset_type=None):
    """ Filter symbols by quoteAsset, return List (all symbols if not specified) """
    symbol_list = []
    for item in exchange_json_obj.get("symbols"):
        if quote_asset_type is None:
            symbol_list += [item.get("symbol")]
        elif quote_asset_type in item.get("quoteAsset"):
            symbol_list += [item.get("symbol")]
    return symbol_list


# TODO: set allowed numbers for limit option
def get_order_book(api_url, symbol, limit):
    """ Get Order Book for a symbol """
    request = make_request(api_url + "depth" + "?symbol=" + symbol +
                           "&limit=" + str(limit))
    return request.json()


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
        symbol_dict[item] = ""

    # ThreadPool the API calls for getting klines.
    # TODO: Make this ThreadPooling a function, maybe don't hard-code workers number?
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []  # Empty List to track Future objects
        for key in symbol_dict:
            futures.append(
                executor.submit(get_kline, api_url=api_url, symbol=key))
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

    # Go do the notional value stuff if requested, otherwise we're done.
    if args.notional is None:
        sys.exit(0)
    else:
        limit = get_order_book_request_limit(args.notional)

        # Define Dicts
        notional_dict = {}
        bids_dict = {}
        asks_dict = {}

        for item in sorted_symbols[0:5]:
            # Add those symbols to a new Dict to get the Order Book JSON for each.
            # FIXME: This one is a wasted Dict, should use a List
            notional_dict[item[0]] = ""
            bids_dict[item[0]] = ""
            asks_dict[item[0]] = ""

    # ThreadPool the API calls for getting order books (see ThreadPool todo above).
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(notional_dict)) as executor:
        futures = []
        for key in notional_dict:
            futures.append(
                executor.submit(get_order_book,
                                api_url=api_url,
                                symbol=key,
                                limit=limit))
        for future in concurrent.futures.as_completed(futures):
            # Populate the dictionary of symbols (keys) with the Order Book value returned
            for key in notional_dict:
                bids_dict[key] = future.result().get("bids")
                asks_dict[key] = future.result().get("asks")
            # Trim to requested amount
            del bids_dict[key][args.notional:]
            del asks_dict[key][args.notional:]

    # Loop through the notional Dict's keys
    for item in notional_dict:
        bids_total = float(0)
        asks_total = float(0)

        # Loop through the bids_dict's List of Lists, summing up price*quantity (notional value)
        for i in bids_dict[item]:
            bids_total += (float(i[0]) * float(i[1]))
        print(item, "total notional value of top", len(bids_dict[item]),
              "bids:", bids_total)

        # Loop through the asks_dict's List of Lists, summing up price*quantity (notional value)
        for i in asks_dict[item]:
            asks_total += (float(i[0]) * float(i[1]))
        print(item, "total notional value of top", len(asks_dict[item]),
              "asks:", asks_total)
        # NOTE: Is this desired too?
        #print(item, "total notional value of both:", (bids_total + asks_total))


# Execute main function
main()
