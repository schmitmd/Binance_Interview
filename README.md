# Assignment questions
- Use public market data from the SPOT API at https://api.binance.com
- Binance API spot documentation is at https://github.com/binance-exchange/binance-official-api-docs/
- All answers should be provided as source code written in either Go, Python and/or Bash.

# Questions:
1. [x] Print the top 5 symbols with quote asset BTC and the highest volume over the last 24 hours in descending order.
  - `main.py --quoteAsset BTC --sort volume`
2. [x] Print the top 5 symbols with quote asset USDT and the highest number of trades over the last 24 hours in descending order.
  - `main.py --quoteAsset USDT --sort trades`
3. [x] Using the symbols from Q1, what is the total notional value of the top 200 bids and asks currently on each order book?
  - `main.py --quoteAsset BTC --sort volume --notional=200`
4. [x] What is the price spread for each of the symbols from Q2?
       Assuming this means "The difference between the highest bid and the lowest ask on the order book"
       (according to https://coinrivet.com/guides/what-is-cryptocurrency-trading/bid-ask-and-bid-ask-spread-prices-what-does-it-all-mean/)
  - `main.py --quoteAsset USDT --sort trades --spread true`
5. [x] Every 10 seconds print the result of Q4 and the absolute delta from the previous value for each symbol.
  - `./main.py --quoteAsset USDT --sort trades --spread true --daemon true`
6. [ ] Make the output of Q5 accessible by querying http://localhost:8080/metrics using the Prometheus Metrics format.
