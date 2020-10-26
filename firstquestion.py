#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Print the top 5 symbols with quote asset BTC and the highest volume over the last 24 hours in descending order."""

import sys

#import argparse
import requests
import simplejson
from pandas import json_normalize

# Parse Arguments
#parser = argparse.ArgumentParser(description="Token Argument.")
#parser.add_argument(
#    "-t",
#    "--token",
#    type=str,
#    help=
#    "A valid token for querying the API",
#    required=False,
#)

#args = parser.parse_args()


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


def sort_json_obj(json_obj, parent_array, sort_by):
    """ Return JSON values sorted """
    data_dump = json_normalize(json_obj[parent_array])

    return data_dump.sort_values([sort_by])


def main():
    """ Main Function """
    api_url = "https://api.binance.com/api/v3/"

    # Basic connectivity check
    make_request(api_url + "ping")

    response = sort_json_obj(
        get_response_as_json(make_request(api_url + "exchangeInfo")),
        "symbols", "quoteAsset")
    print(response)


# Execute main function
main()
