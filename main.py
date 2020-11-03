#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Binance Interview """

import concurrent.futures
import sys
import argparse
import datetime
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
    "-s",
    "--sort",
    type=str,
    help="Sort top values by",
    choices=['volume', 'trades'],
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


def get_kline(api_url, symbol, endtime_ms, starttime_ms, interval="1m"):
    """ Return List of klines for a passed symbol and interval (default to 1min
        interval) between a startTime and an endTime in milliseconds
    """
    kline = make_request(
        str(api_url) + "klines" + "?symbol=" + str(symbol) + "&interval=" +
        str(interval) + "&endTime=" + str(endtime_ms) + "&startTime=" +
        str(starttime_ms))

    # FIXME: should use get_response_as_json func?
    return list(kline.json())


def get_order_book_request_limit(limit):
    """ Return a valid request limit parameter (int) for the order book API endpoint """
    valid_limits = [5, 10, 20, 50, 100, 500, 1000, 5000]
    for value in valid_limits:
        if limit <= value:
            return value
    sys.exit("The maximum number of top bids/asks you can request is " +
             str(valid_limits[-1]))


def get_offset_time_in_milliseconds():
    """ Return current time in milliseconds """
    # FIXME: Allow specifying timezone like "America/Denver", don't force UTC timezone
    # Get epoch (assume UTC by default)
    epoch = datetime.datetime.utcfromtimestamp(0).replace(
        tzinfo=datetime.timezone.utc)

    # Get current time (assume UTC by default)
    now = datetime.datetime.now(datetime.timezone.utc)

    # Get time from 24h ago epoch (assume UTC by default)
    day_ago = (now - datetime.timedelta(hours=24))

    # Return the difference in milliseconds
    return (int((now - epoch).total_seconds() * 1000.0),
            int((day_ago - epoch).total_seconds() * 1000.0))


def sort_klines_by_volume(kline_list_obj):
    """ Sort kline List of Lists object by Volume in sub-Lists """
    # TODO: Make a struct or something to sort by an arbitrary value in klines List instead of hard-coding the 7th element here
    return sorted(kline_list_obj, key=lambda x: x[6], reverse=True)


def sort_klines_by_trades(kline_list_obj):
    """ Sort kline List of Lists object by Number of Trades in sub-Lists """
    # TODO: Make a struct or something to sort by an arbitrary value in klines List instead of hard-coding the 9th element here
    return sorted(kline_list_obj, key=lambda x: x[8], reverse=True)


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


def get_sorted_symbols_by_trades(symbol_dict):
    """ Return a List of passed Dict keys sorted by 9th element (Number of Trades) in sorted List of Sub-Lists """
    for i in symbol_dict:
        symbol_dict[i] = sort_klines_by_trades(symbol_dict[i])
    # Get a List of the Dict keys sorted by 9th element (Number of Trades) in each
    # sub-List of the first List item by symbol (already know first List item is
    # highest volume per symbol thanks to above sort_klines_by_trades() call
    # {"ETHBTC": [(_1_)[(_0_)0,1,2,3,4,5,6,7,8(_8_),9,10],[0,1,2,3,4,5,6,7,8(_8_),9,10]]}
    sorted_symbols = sorted(symbol_dict.items(),
                            key=lambda x: x[1][0][8],
                            reverse=True)
    return sorted_symbols


def get_sorted_symbols_by_volume(symbol_dict):
    """ Return a List of passed Dict keys sorted by 7th element (Volume) in first entry of List of Sub-Lists """
    for i in symbol_dict:
        symbol_dict[i] = sort_klines_by_volume(symbol_dict[i])
    # Get a List of the Dict keys sorted by 7th element (Volume) in each
    # sub-List of the first List item by symbol (already know first List item is
    # highest volume per symbol thanks to above sort_klines_by_volume() call
    # {"ETHBTC": [(_1_)[(_0_)0,1,2,3,4,5,6(_6_),7,8,9,10],[0,1,2,3,4,5,6,7,8,9,10]]}
    sorted_symbols = sorted(symbol_dict.items(),
                            key=lambda x: x[1][0][6],
                            reverse=True)
    return sorted_symbols


def notional_get(symbol_dict, api_url, get_type, limit):
    """ Get Order Book for a symbol, filtering by type (bids/asks) as passed """
    # ThreadPool the API calls for getting order books (see ThreadPool todo above).
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(symbol_dict)) as executor:
        futures = (executor.submit(get_order_book,
                                   api_url=api_url,
                                   symbol=key,
                                   limit=limit) for key in symbol_dict)
        for future in concurrent.futures.as_completed(futures):
            # Populate the dictionary of symbols (keys) with the Order Book value returned
            for key in symbol_dict:
                symbol_dict[key] = future.result().get(str(get_type))
    return symbol_dict


def main():
    """ Main Function """

    # Set base API URL
    api_url = "https://api.binance.com/api/v3/"

    # Basic connectivity check
    make_request(api_url + "ping")

    # Get 24h time offset for kline API data calls
    now_ms, day_ago_ms = get_offset_time_in_milliseconds()

    # Get exchangeInfo as JSON
    exchange = get_response_as_json(make_request(api_url + "exchangeInfo"))

    # Populate symbols list by searching through exchangeInfo for quoteAssets of type args.quoteAsset
    symbol_list = find_symbols_by_quote_asset(exchange, args.quoteAsset)

    # Make a dictionary with the keys being symbols from the symbol_list above
    # Lists (which will be populated below as Lists of Lists by getting the
    # klines for each symbol)
    symbol_dict = dict.fromkeys(symbol_list, None)

    # ThreadPool the API calls for getting klines.
    # TODO: Make this ThreadPooling a function, maybe don't hard-code workers number?
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = (executor.submit(get_kline,
                                   api_url=api_url,
                                   symbol=key,
                                   starttime_ms=day_ago_ms,
                                   endtime_ms=now_ms) for key in symbol_dict)
        for future in concurrent.futures.as_completed(futures):
            for key in symbol_dict:
                # Sort the List of Lists by Volume element in sub-lists, save.
                symbol_dict[key] = future.result()

    sorted_symbols = []
    if args.sort == 'volume':
        for i in symbol_dict:
            symbol_dict[i] = sort_klines_by_volume(symbol_dict[i])
        sorted_symbols = get_sorted_symbols_by_volume(symbol_dict)
        print("Top 5 symbols by Volume over the last 24h")
    elif args.sort == 'trades':
        for i in symbol_dict:
            symbol_dict[i] = sort_klines_by_trades(symbol_dict[i])
        sorted_symbols = get_sorted_symbols_by_trades(symbol_dict)
        print("Top 5 symbols by Number of Trades over the last 24h")

    # Print the results
    for item in sorted_symbols[0:5]:
        print(item[0])

    # Go do the notional value stuff if requested, otherwise we're done.
    if args.notional is None:
        sys.exit(0)
    else:
        limit = get_order_book_request_limit(args.notional)

    bids_dict, asks_dict = {}, {}
    # Print the results
    for item in sorted_symbols[0:5]:
        bids_dict[item[0]] = None
        asks_dict[item[0]] = None
    bids_dict = notional_get(bids_dict, api_url, "bids", limit)
    asks_dict = notional_get(asks_dict, api_url, "asks", limit)

    # Trim to requested amount
    for key in bids_dict:
        del bids_dict[key][args.notional:]
    for key in asks_dict:
        del asks_dict[key][args.notional:]

    # Loop through the Dict's keys FIXME: This is wrong
    for item in bids_dict:
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
