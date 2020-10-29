# Assignment questions
- Use public market data from the SPOT API at https://api.binance.com
- Binance API spot documentation is at https://github.com/binance-exchange/binance-official-api-docs/
- All answers should be provided as source code written in either Go, Python and/or Bash.

# Questions:
1. [x] Print the top 5 symbols with quote asset BTC and the highest volume over the last 24 hours in descending order.
  - `main.py --quoteAsset BTC`
2. [x] Print the top 5 symbols with quote asset USDT and the highest number of trades over the last 24 hours in descending order.
  - `main.py --quoteAsset USDT`
3. [ ] Using the symbols from Q1, what is the total notional value of the top 200 bids and asks currently on each order book?
4. [ ] What is the price spread for each of the symbols from Q2?
5. [ ] Every 10 seconds print the result of Q4 and the absolute delta from the previous value for each symbol.
6. [ ] Make the output of Q5 accessible by querying http://localhost:8080/metrics using the Prometheus Metrics format.
