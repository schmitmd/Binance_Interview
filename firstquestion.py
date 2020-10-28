#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Print the top 5 symbols with quote asset BTC and the highest volume over the last 24 hours in descending order."""

import sys

import argparse
import requests
import simplejson
# TODO: Use the community binance python lib
# from binance.client import Client

# Parse Arguments
parser = argparse.ArgumentParser(
    description=
    "Print the top 5 symbols with quote asset BTC and the highest volume over the last 24 hours in descending order."
)
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
args = parser.parse_args()


def make_request(url):
    """  Hit a URL and return a requests object iff the return code was 200 OK """
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


def get_kline(api_url, symbol, interval):
    """ Return JSON values sorted """
    kline = make_request(api_url + "klines" + "?symbol=" + symbol +
                         "&interval=" + interval)
    return kline


def sort_klines_by_volume(kline_list_obj):
    """ Sort kline List of Lists object by Volume in sub-Lists """
    # TODO: Make a struct or something to sort by an arbitrary value in klines List instead of hard-coding the 6th element here
    return sorted(kline_list_obj, key=lambda x: x[5], reverse=True)


def main():
    """ Main Function """

    # Set base API URL
    api_url = "https://api.binance.com/api/v3/"

    # Basic connectivity check
    make_request(api_url + "ping")

    # Initialize an empty List of symbols to get klines for
    symbols_to_check = []

    # Get exchangeInfo, loop through symbols searching for quoteAssets that are "BTC", add them to the symbols_to_check List
    exchange = get_response_as_json(make_request(api_url + "exchangeInfo"))
    for item in exchange.get("symbols"):
        if "BTC" in item.get("quoteAsset"):
            symbols_to_check += [item.get("symbol")]

    # This will be a List of Lists per Binance API spec https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#klinecandlestick-data
    kline_results = []

    # Get the klines for the last 24h for each symbol
    for symbol in symbols_to_check:
        # FIXME: Use JSON instead of a List of a bunch of sub-Lists
        kline_results.append(get_kline(api_url, symbol, "1d").text)

    #print(kline_results[1])

    # Now we need to check values of the sub-lists in kline_results List
    #print(sort_klines_by_volume(kline_results))


# Execute main function
main()
