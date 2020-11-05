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
    default='volume',
    required=False,
)
parser.add_argument(
    "-n",
    "--notional",
    type=int,
    help="Number of top bids and asks to get notional values for by symbol",
    required=False,
)
parser.add_argument(
    "--spread",
    type=bool,
    help="Show price spread of symbols",
    required=False,
)
parser.add_argument(
    "--daemon",
    type=bool,
    help="Print data every 10 seconds",
    required=False,
)
parser.add_argument(
    "-t",
    "--top",
    type=int,
    default=5,
    help="Number of top symbols to show",
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


def get_kline(api_url, symbol, endtime_ms, starttime_ms, interval="1d"):
    """ Return List of klines for a passed symbol and interval (default to 1min
        interval) between a startTime and an endTime in milliseconds
    """
    kline = make_request(
        str(api_url) + "klines" + "?symbol=" + str(symbol) + "&interval=" +
        str(interval) + "&endTime=" + str(endtime_ms) + "&startTime=" +
        str(starttime_ms))

    # FIXME: should use get_response_as_json func?
    return list(kline.json())


def get_order_book_request_limit(limit=100):
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
def get_order_book(api_url, symbol, limit=100):
    """ Get Order Book for a symbol """
    request = make_request(api_url + "depth" + "?symbol=" + symbol +
                           "&limit=" + str(limit))
    return request.json()


def get_sorted_symbols_by_trades(symbol_dict):
    """ Return a List of passed Dict keys sorted ascending by 9th element (Number of Trades) in first entry of List of Sub-Lists """
    # Get a List of the Dict keys sorted by 9th element (Number of Trades) in each
    # sub-List of the first List item by symbol (already know first List item is
    # highest volume per symbol thanks to above sort_klines_by_trades() call
    # {"ETHBTC": [(_1_)[(_0_)0,1,2,3,4,5,6,7,8(_8_),9,10],[0,1,2,3,4,5,6,7,8(_8_),9,10]]}
    return sorted(symbol_dict.items(), key=lambda x: x[1][0][8], reverse=True)


def get_sorted_symbols_by_volume(symbol_dict):
    """ Return a List of passed Dict keys sorted ascending by 7th element (Volume) in first entry of List of Sub-Lists """
    # Get a List of the Dict keys sorted by 7th element (Volume) in each
    # sub-List of the first List item by symbol (already know first List item is
    # highest volume per symbol thanks to above sort_klines_by_volume() call
    # {"ETHBTC": [(_1_)[(_0_)0,1,2,3,4,5,6(_6_),7,8,9,10],[0,1,2,3,4,5,6,7,8,9,10]]}

    return sorted(symbol_dict.items(), key=lambda x: x[1][0][6], reverse=True)


def sort_by_price(list_obj):
    """ Return a List of Lists object in descending order sorted by 1st element (price) in Sub-Lists """
    # TODO: Make a struct or something to sort by price or quantity
    return sorted(list_obj, key=lambda x: x[0], reverse=True)


def notional_get(symbol_dict, api_url, get_type, limit):
    """ Get Order Book for a symbol, filtering by type (bids/asks) as passed """
    # ThreadPool the API calls for getting order books.
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_order_book,
                            api_url=api_url,
                            symbol=key,
                            limit=limit): key
            for key in symbol_dict
        }
        for future in concurrent.futures.as_completed(futures):
            # Populate the dictionary of symbols (keys) with the Order Book value returned
            # FIXME!!: This is a BUG! Order book should never return empty sets
            if future.result() == []:
                del symbol_dict[futures[future]]
            else:
                symbol_dict[futures[future]] = future.result().get(
                    str(get_type))
    return symbol_dict


def get_total_notional_value(list_obj):
    """ Return float value sum of price*quantity of List of Sub-Lists by Dictionary object key (symbol) """
    running_total = float(0)
    # Loop through List of Lists, summing up price*quantity (=notional value)
    for i in list_obj:
        running_total += (float(i[0]) * float(i[1]))
    return running_total


def print_notional_value(orders_dict, name):
    """ Print data in a Dict containing a List of Lists by notional value """
    # TODO: Use a single Dict for both bids and asks
    for item in orders_dict:
        print("Total notional value for top", len(orders_dict[item]),
              str(name), "for symbol", item, ":",
              get_total_notional_value(orders_dict[item]))
    # NOTE: Is this desired too?
    #print(item, "total notional value of both:", (bids_total + asks_total))


def sort_dict_by_price(dict_obj):
    """ Sort Dict keys by price in List of Lists data, see
    https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#order-book """
    # Sort the bids Dict by price
    for key in dict_obj:
        dict_obj[key] = sort_by_price(dict_obj[key])


def populate_klines(dict_obj, api_url, starttime_ms, endtime_ms):
    """ Populate the passed Dict object with kline values for each symbol (Dict key) by startTime and endTime """
    # ThreadPool execute kline fetches for each symbol
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_kline,
                            api_url=api_url,
                            symbol=key,
                            starttime_ms=starttime_ms,
                            endtime_ms=endtime_ms): key
            for key in dict_obj
        }

        for future in concurrent.futures.as_completed(futures):
            # FIXME!!: This is a BUG! Klines should never return empty sets
            if future.result() == []:
                del dict_obj[futures[future]]
            else:
                dict_obj[futures[future]] = future.result()


def print_top_symbols(symbols_list):
    """ Print out the first item (symbol) in the passed List based on --top argument """
    # Print the results
    print("Top ", args.top, "symbols by", args.sort.capitalize(),
          "over the last 24h")
    for item in symbols_list[0:args.top]:
        print(item[0])


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

    # Make a dictionary with the keys being symbols from the symbol_list above
    # Lists (which will be populated below as Lists of Lists by getting the
    # klines for each symbol)
    symbol_dict = dict.fromkeys(symbol_list, None)

    # Get 24h time offset for kline API data calls in milliseconds
    now_ms, day_ago_ms = get_offset_time_in_milliseconds()

    # Populate the kline values in the symbol_dict
    populate_klines(symbol_dict, api_url, day_ago_ms, now_ms)

    # Aggregate volume or number of trades based on command arguments
    if args.sort == 'volume':
        for i in symbol_dict:
            symbol_dict[i] = sort_klines_by_volume(symbol_dict[i])
        sorted_symbols = get_sorted_symbols_by_volume(symbol_dict)
        # Print results
        print_top_symbols(sorted_symbols)
    elif args.sort == 'trades':
        for i in symbol_dict:
            symbol_dict[i] = sort_klines_by_trades(symbol_dict[i])
        sorted_symbols = get_sorted_symbols_by_trades(symbol_dict)
        print_top_symbols(sorted_symbols)

    # Go do the notional value stuff if requested, otherwise we're done.
    if args.notional is None and args.spread is None:
        sys.exit(0)
    elif args.notional is not None:
        limit = get_order_book_request_limit(args.notional)
    else:
        limit = get_order_book_request_limit()

    # FIXME: These shouldn't be separate Dicts, this makes two separate
    # calls to notional_get(), one for bids and one for asks.
    # Seed new Dicts with the top symbols returned above
    #bids_dict = dict.fromkeys(symbol_list[0:args.top], None)
    #asks_dict = dict.fromkeys(symbol_list[0:args.top], None)
    bids_dict, asks_dict = {}, {}
    for item in sorted_symbols[0:args.top]:
        bids_dict[item[0]] = None
        asks_dict[item[0]] = None
        #print(item[0])

    # Populate Dicts with bids/asks
    bids_dict = notional_get(bids_dict, api_url, "bids", limit)
    asks_dict = notional_get(asks_dict, api_url, "asks", limit)

    if args.notional is not None:
        # Trim to requested amount
        for key in bids_dict:
            del bids_dict[key][args.notional:]
        for key in asks_dict:
            del asks_dict[key][args.notional:]

    # Loop through the Dict, printing the total notional value per symbol
    print_notional_value(bids_dict, "bids")
    print_notional_value(asks_dict, "asks")
    # NOTE: Is this desired too?
    #print(item, "total notional value of both:", (bids_total + asks_total))

    if args.spread:
        sort_dict_by_price(bids_dict)
        sort_dict_by_price(asks_dict)

        # Print the results (difference between highest bid price and lowest ask price)
        for key in bids_dict:
            print("Price spread for", key, ":",
                  (float(bids_dict[key][0][0]) - float(asks_dict[key][-1][0])))


# Execute main function
main()
