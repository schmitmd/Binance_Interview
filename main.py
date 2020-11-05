#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Binance Interview """

import concurrent.futures
import sys
import argparse
import datetime
import time
import requests

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

# Set base API URL
API_BASE_URL = "https://api.binance.com/api/v3/"

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


def get_kline(symbol, endtime_ms, starttime_ms, interval="1d"):
    """ Return List of klines for a passed symbol and interval (default to 1min
        interval) between a startTime and an endTime in milliseconds
    """
    kline = make_request(
        str(API_BASE_URL) + "klines" + "?symbol=" + str(symbol) +
        "&interval=" + str(interval) + "&endTime=" + str(endtime_ms) +
        "&startTime=" + str(starttime_ms))

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


def sort_klines(kline_list_obj):
    """ Sort kline List of Lists object by args.sort in sub-Lists """
    # TODO: Make a struct or something to sort by an arbitrary value in klines List instead of hard-coding specific elements by arg value here
    if args.sort == 'volume':
        sortby = 6
    elif args.sort == 'trades':
        sortby = 8
    return sorted(kline_list_obj, key=lambda x: x[sortby], reverse=True)


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
def get_order_book(symbol, limit=100):
    """ Get Order Book for a symbol """
    request = make_request(API_BASE_URL + "depth" + "?symbol=" + symbol +
                           "&limit=" + str(limit))
    return request.json()


def get_sorted_symbols(symbol_dict):
    """ Return a List of passed Dict keys sorted ascending by args.sort element in first entry of List of Sub-Lists """
    # TODO: Make a struct or something to sort by an arbitrary value in List instead of hard-coding specific elements by arg value here
    if args.sort == 'volume':
        sortby = 6
    elif args.sort == 'trades':
        sortby = 8
    return sorted(symbol_dict.items(),
                  key=lambda x: x[1][0][sortby],
                  reverse=True)


def sort_by_price(list_obj):
    """ Return a List of Lists object in descending order sorted by 1st element (price) in Sub-Lists """
    # TODO: Make a struct or something to sort by price or quantity
    return sorted(list_obj, key=lambda x: x[0], reverse=True)


def notional_get(symbol_dict, get_type, limit):
    """ Get Order Book for a symbol, filtering by type (bids/asks) as passed """
    # ThreadPool the API calls for getting order books.
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_order_book, symbol=key, limit=limit): key
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


def populate_klines(dict_obj, starttime_ms, endtime_ms):
    """ Populate the passed Dict object with kline values for each symbol (Dict key) by startTime and endTime """
    # ThreadPool execute kline fetches for each symbol
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_kline,
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


def process_klines(symbol_dict):
    """ Process last 24 hours of kline data by symbol in passed Dict """
    # Get 24h time offset for kline API data calls in milliseconds
    now_ms, day_ago_ms = get_offset_time_in_milliseconds()

    # Populate the kline values in the symbol_dict
    populate_klines(symbol_dict, day_ago_ms, now_ms)

    # Aggregate volume or number of trades based on command arguments
    for i in symbol_dict:
        symbol_dict[i] = sort_klines(symbol_dict[i])


def process_order_book_dict(sorted_symbols, order_book_type, limit):
    """ Create and return a Dict corresponding to the Order Book output per symbol (key) by type in a passed List """
    dict_obj = {item[0]: None for item in sorted_symbols[0:args.top]}
    dict_obj = notional_get(dict_obj, str(order_book_type), limit)
    return dict_obj


def trim_dict(dict_obj):
    """ Trim each value (List of Lists) in a passed Dict down to args.notional if defined """
    if args.notional is not None:
        # Trim to requested amount
        for key in dict_obj:
            del dict_obj[key][args.notional:]
    return dict_obj


def main():
    """ Main Function """
    # Basic connectivity check
    make_request(API_BASE_URL + "ping")

    # Get exchangeInfo as JSON
    exchange = make_request(API_BASE_URL + "exchangeInfo").json()

    # Populate symbols List by searching through exchangeInfo for quoteAssets of type args.quoteAsset
    symbol_list = find_symbols_by_quote_asset(exchange, args.quoteAsset)

    # Make a dictionary with the keys being symbols from the symbol_list above
    # Lists (which will be populated below as Lists of Lists by getting the
    # klines for each symbol)
    symbol_dict = dict.fromkeys(symbol_list, None)

    if args.daemon:
        # One-time creation of last_spreads dict
        last_spreads_dict = {}
        while True:
            # Do kline processing
            process_klines(symbol_dict)

            # Get sorted List of symbols based on args.sort
            sorted_symbols = get_sorted_symbols(symbol_dict)

            # Print results
            print_top_symbols(sorted_symbols)

            # Go do the notional value stuff if requested, otherwise we're done.
            if args.notional is None:
                if args.spread is None:
                    sys.exit(
                        "Cannot have both --spread and --notional undefined")
                else:
                    limit = get_order_book_request_limit()
            else:
                limit = get_order_book_request_limit(args.notional)

            # Seed new Dicts with the top symbols returned above
            # FIXME: These shouldn't be separate Dicts, this makes two separate
            # calls to notional_get(), one for bids and one for asks.
            bids_dict = process_order_book_dict(sorted_symbols, "bids", limit)
            asks_dict = process_order_book_dict(sorted_symbols, "asks", limit)
            trim_dict(bids_dict)
            trim_dict(asks_dict)

            # Loop through the Dict, printing the total notional value per symbol
            print_notional_value(bids_dict, "bids")
            print_notional_value(asks_dict, "asks")
            # NOTE: Is this desired too?
            #print(item, "total notional value of both (by symbol):", (bids_total + asks_total))

            # Check for --spread argument, print price spread per-symbol if True
            if args.spread:
                sort_dict_by_price(bids_dict)
                sort_dict_by_price(asks_dict)

                # Make a new Dict from keys in bids_dict (see fixme above about two separate dicts)
                spreads_dict = dict.fromkeys(bids_dict)
                # Print the results (difference between highest bid price and lowest ask price)
                for key in spreads_dict:
                    spreads_dict[key] = (float(bids_dict[key][0][0]) -
                                         float(asks_dict[key][-1][0]))
                    print("Price spread for", key, ":", spreads_dict[key])

                    # FIXME: This is an if check to overcome a bad assumption
                    # (what if the symbols list from kline values above changes between runs?)
                    if key in last_spreads_dict:
                        print(
                            "Absolute delta of price spread from last pull for",
                            key, ":",
                            float(spreads_dict[key] - last_spreads_dict[key]))

                last_spreads_dict = spreads_dict

            time.sleep(10)

    # Do kline processing
    process_klines(symbol_dict)

    # Get sorted List of symbols based on args.sort
    sorted_symbols = get_sorted_symbols(symbol_dict)

    # Print results
    print_top_symbols(sorted_symbols)

    # Go do the notional value stuff if requested, otherwise we're done.
    if args.notional is None:
        if args.spread is None:
            sys.exit(0)
        else:
            limit = get_order_book_request_limit()
    else:
        limit = get_order_book_request_limit(args.notional)

    # Seed new Dicts with the top symbols returned above
    # FIXME: These shouldn't be separate Dicts, this makes two separate
    # calls to notional_get(), one for bids and one for asks.
    bids_dict = process_order_book_dict(sorted_symbols, "bids", limit)
    asks_dict = process_order_book_dict(sorted_symbols, "asks", limit)
    trim_dict(bids_dict)
    trim_dict(asks_dict)

    # Loop through the Dict, printing the total notional value per symbol
    print_notional_value(bids_dict, "bids")
    print_notional_value(asks_dict, "asks")
    # NOTE: Is this desired too?
    #print(item, "total notional value of both (by symbol):", (bids_total + asks_total))

    # Check for --spread argument, print price spread per-symbol if True
    if args.spread:
        sort_dict_by_price(bids_dict)
        sort_dict_by_price(asks_dict)

        # Make a new Dict from keys in bids_dict (see fixme above about two separate dicts)
        spreads_dict = dict.fromkeys(bids_dict)
        # Print the results (difference between highest bid price and lowest ask price)
        for key in spreads_dict:
            spreads_dict[key] = (float(bids_dict[key][0][0]) -
                                 float(asks_dict[key][-1][0]))
            print("Price spread for", key, ":", spreads_dict[key])


# Execute main function
main()
