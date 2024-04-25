## bittrex.py by Ryan Farber 23 November 2017
"""
The purpose of this script is to get the current value of my
cryptocurrency holdings on bittrex, in btc and in usd.

The below was modified from:
https://github.com/ericsomdahl/python-bittrex/blob/master/bittrex/bittrex.py
check it out if you get stuck trying to do something.
"""
from urllib.parse import urlencode
import os
import numpy as np
import sys
import time,hmac,hashlib
import datetime

try: # successful for Anaconda 4.3.30 Python 3.6.3
  from Crypto.Cipher import AES
except ImportError:
  encrypted = False
else: # executes for Anaconda 4.3.30 Python 3.6.3
  import getpass
  import ast
  import json
  encrypted = True
# end try/except/else

import requests


class bittrex(object):
  def __init__(self):
    api_url = "https://bittrex.com/api/"
    api_v   = "v1.1"
    self.base_url = api_url + api_v

    self.view_key = os.environ[""]
    self.limit_key = os.environ[""]

    self.end_url_view  = "apikey="  + self.view_key
    self.end_url_limit  = "apikey=" + self.limit_key

    self._init_session()
    self.need_speed = True
    self.best_arbs_cnt = 0
    self.my_id = str(np.random.random(1)[0])[2:]
  # end init

  def _init_session(self):
    self.session = requests.session()
  # end _init_session

  def _sign(self, url):
    if   self.view_key  in url:
      secret = os.environ[""]
    elif self.limit_key in url:
      secret = os.environ[""]
    # end if/elif
    return hmac.new(secret.encode(), url.encode(), 
                      hashlib.sha512).hexdigest()
  # end _sign

  def _get(self, url):
    if self.need_speed == False:
      time.sleep(1.1)
    # end if

    old_url = url
    success = False
    while success == False:
      nonce = str(int(time.time()*1000))
      url = old_url + "&nonce=" + nonce

      url_sig = self._sign(url)
      header = {"apisign":url_sig}
      self.session.headers.update(header)

      try:
        # note, timeout is in seconds
        r = getattr(self.session, "get")(url, timeout=1.0)
      except requests.ConnectionError as e:
        print("ConnectionError: ", e)
        fname = "connectionError_" + self.my_id + ".txt"
        with open(fname, "a") as fid_get:
          fid_get.write("ConnectionError, trying again. ")
        # end with
        continue
      except requests.Timeout as e:
        print("Timeout: ", e)
        fname = "timeout_" + self.my_id + ".txt"
        with open(fname, "a") as fid_get:
          fid_get.write("Timeout, trying again. ")
        # end with
        continue
      # end try/except
      print(r)
      print(r.text)

      if r.status_code in [502,503,504,524]:
        continue
      # end if

      fname = "responseJson_" + self.my_id + ".txt"
      with open(fname, "w") as fid_get:
        fid_get.write(r.text)
      # end with

      if r.json()["message"] == "APIKEY_INVALID":
        fname = "apikeyInvalidError_" + self.my_id + ".txt"
        with open(fname, "a") as fid_get:
          fid_get.write("APIKEY_INVALID, trying again. ")
        continue
      # end if

      success = True
    # end while

    return r.json()["result"]
  # end _get

  def get_balances(self):
    url = self.base_url + "/account/getbalances?" + self.end_url_view
    account = self._get(url)

    self.currencies = {}
    for currency in account:
      self.currencies[currency["Currency"]] = {"balance":currency["Balance"]}
    # end for
  # end get_balances

  def display_balances(self):
    self.get_balances()
    for currency in self.currencies:
      print(currency, self.currencies[currency])
    # end for
  # end display_balances

  def get_btc_per(self):
    self.get_balances()
    url = self.base_url + "/public/getmarketsummaries?" + self.end_url_view
    marketsummaries = self._get(url)
    for marketsummary in marketsummaries:
      if   marketsummary["MarketName"].split("-")[0] == "BTC":
        currency = marketsummary["MarketName"].split("-")[1]
        if currency in self.currencies.keys():
          self.currencies[currency]["btc_per"] = marketsummary["Bid"]
        # end if
      elif marketsummary["MarketName"].split("-")[1] == "BTC":
        currency = marketsummary["MarketName"].split("-")[0]
        btc_per = 1.0 / marketsummary["Bid"]
        if currency in self.currencies.keys():
          self.currencies[currency]["btc_per"] = btc_per
        else:
          self.currencies[currency] = {"balance":0.0, "btc_per": btc_per}
        # end if/else
      # end if/elif
    # end for
  # end get_btc_per

  def get_balances_in_usd(self):
    self.get_btc_per()
    usd_per_btc = 1.0 / self.currencies["USD"]["btc_per"]
    for currency in self.currencies.keys():
      if currency == "BTC":
        self.currencies[currency]["value_in_usd"] = \
          self.currencies[currency]["balance"] * usd_per_btc
      else:
        if "btc_per" not in self.currencies[currency].keys():
          print(currency + " is not currently traded on Bittrex."
                         + " Check Binance.")
        else:
          self.currencies[currency]["value_in_usd"] = \
            self.currencies[currency]["balance"] * \
            self.currencies[currency]["btc_per"] * usd_per_btc
      # end if/else
    # end for
  # end get_balances_in_usd

  def display_balances_in_usd(self):
    self.get_balances_in_usd()
    for currency in self.currencies.keys():
      if "value_in_usd" not in self.currencies[currency].keys():
        print(currency + " is not currently traded on Bittrex."
                       + " Check Binance.")
      else:
        print(currency, "$" + str(self.currencies[currency]["value_in_usd"]))
      # end if/else
    # end for
  # end display_balances_in_usd

  def get_total_value_in_usd(self):
    self.get_balances_in_usd()
    usd = 0.0
    for currency in self.currencies:
      if "value_in_usd" not in self.currencies[currency].keys():
        continue
      # end if
      usd += self.currencies[currency]["value_in_usd"]
    # end for
    self.total_value_in_usd = usd
  # end get_total_value_in_usd

  def display_total_value_in_usd(self):
    self.get_total_value_in_usd()
    print("Total value in bittrex in usd: ", self.total_value_in_usd)
  # end display_total_value_in_usd

  def get_maxMinTradeValue(self):
    self.get_btc_per()

    url = self.base_url + "/public/getmarkets?" + self.end_url_view
    markets = self._get(url)

    url = self.base_url + "/public/getmarketsummaries?" + self.end_url_view
    msums   = self._get(url)

    self.bad_names = []
    max_value = 0.0
    for market in markets:
      name = market["MarketName"]
      for msum in msums:
        if msum["MarketName"] == name:
          break
        # end if
      # end for
      max_rate = 1.0001 * msum["Ask"]
      value = market["MinTradeSize"] * max_rate

      name0 = name.split("-")[0]
      if name0 != "BTC":
        if name0 not in self.currencies.keys():
          print("Error! New market! Deal with it.")
          print("name: ", name)
          sys.exit()
        # end if

        if "btc_per" not in self.currencies[name0].keys():
          print("Error! New market! Deal with it.")
          print("name: ", name)
          sys.exit()
        # end if
        value *= self.currencies[name0]["btc_per"]
      # end if

      if   value > 0.0018:
        print("bad_market: ", name, "because minValue: ", value)
        self.bad_names.append(name.split("-")[1])
      elif value > max_value:
        max_value = value
      # end if
    # end for
    max_value += 10**(np.floor(np.log10(max_value))-1.0)
    max_value  = max(max_value, 0.0010)

    self.value = max_value
  # end get_maxMinTradeValue

  def get_triplets(self):
    self.get_maxMinTradeValue()

    url = self.base_url + "/public/getmarketsummaries?" + self.end_url_view
    marketsummaries = self._get(url)

    names = []
    asks  = []
    bids  = []
    triplets = []
    triplets_asks = []
    triplets_bids = []   
    for marketsummary in marketsummaries:
      name = marketsummary["MarketName"]
      name0, name1 = name.split("-")
      if name1 in self.bad_names:
        continue
      # end if
      ask  = marketsummary["Ask"]
      bid  = marketsummary["Bid"]

      inds = [i for i, s in enumerate(names) if name1 in s.split("-")]
      if len(inds) == 0:
        names.append(name)
        asks.append(ask)
        bids.append(bid)
        continue
      # end if

      pairs     = [name]
      pair_asks = [ask]
      pair_bids = [bid]
      for ind in inds:
        pairs.append(   names[ind])
        pair_asks.append(asks[ind])
        pair_bids.append(bids[ind])
      # end for

      if len(pairs) == 2:
        if pairs[0].split("-")[0] not in ["BTC", "ETH"]:
          continue
        # end if
        triplets.append(pairs)
        triplets_asks.append(pair_asks)
        triplets_bids.append(pair_bids)
      elif len(pairs) == 3:
        continue
        triplets.append([pairs[0], pairs[1]])
        triplets.append([pairs[0], pairs[2]])
        triplets_asks.append([pair_asks[0], pair_asks[1]])
        triplets_asks.append([pair_asks[0], pair_asks[2]])
        triplets_bids.append([pair_bids[0], pair_bids[1]])
        triplets_bids.append([pair_bids[0], pair_bids[2]])
      # end if/elif

      names.append(name)
      asks.append(ask)
      bids.append(bid)
    # end for marketsummaries
    return names, bids, asks, triplets, triplets_asks, triplets_bids
  # end get_triplets

  def get_arbitrage_profit_fwd(self, rate_1per2, rate_3per2, rate_3per1):
    c1 = 1.0
    c2 = c1 / rate_1per2
    c3 = c2 * rate_3per2
    c1 = c3 / rate_3per1
    return (c1 - 1.0) / 1.0
  # end get_arbitrage_profit_fwd

  def get_arbitrage_profit_bwd(self, rate_1per2, rate_3per2, rate_3per1):
    c3 = 1.0
    c2 = c3 / rate_3per2
    c1 = c2 * rate_1per2
    c3 = c1 * rate_3per1

    return (c3 - 1.0) / 1.0
  # end get_arbitrage_profit_bwd

  def get_best_arbitrage(self):
    self.arb_names = ["max", "mid", "i1mid2max3", "i1mid2max+0.01%3",
                      "i12max3", "instant"]
    the_triplets   = [[] for i in range(len(self.arb_names))]
    the_profits    = [[] for i in range(len(self.arb_names))]
    the_rates      = [[] for i in range(len(self.arb_names))]
    the_quantities = [[] for i in range(len(self.arb_names))]

    names, bids, asks, triplets, triplets_asks, triplets_bids = \
                                              self.get_triplets()
    for i in range(len(triplets)):
      triplet = triplets[i]
      triplet_asks = triplets_asks[i]
      triplet_bids = triplets_bids[i]

      third_first = triplet[1].split("-")[0] + "-" + \
                    triplet[0].split("-")[0]
      if   third_first == "BTC-USDT":
        third_first = "USDT-BTC"
        ind = names.index(third_first)
        ask_31 = 1.0/asks[ind]
        bid_31 = 1.0/bids[ind]
      elif third_first == "ETH-USDT":
        third_first= "USDT-ETH"
        ind = names.index(third_first)
        ask_31 = 1.0/asks[ind]
        bid_31 = 1.0/bids[ind]
      else:
        ind = names.index(third_first)
        ask_31 = asks[ind]
        bid_31 = bids[ind]
      # end if

      triplet_fwd = triplet[0].split("-")[0] + "-" + \
                    triplet[0].split("-")[1] + "-" + \
                    triplet[1].split("-")[0]

      triplet_bwd = triplet[1].split("-")[0] + "-" + \
                    triplet[0].split("-")[1] + "-" + \
                    triplet[0].split("-")[0]

      rates_1per2_fwd = np.zeros(len(self.arb_names))
      rates_3per2_fwd = np.zeros(len(self.arb_names))
      rates_3per1_fwd = np.zeros(len(self.arb_names))
      rates_1per2_bwd = np.zeros(len(self.arb_names))
      rates_3per2_bwd = np.zeros(len(self.arb_names))
      rates_3per1_bwd = np.zeros(len(self.arb_names))

      k = 0
      ## max profit
      rates_1per2_fwd[k] = triplet_bids[0]
      rates_3per2_fwd[k] = triplet_asks[1]
      rates_3per1_fwd[k] = bid_31
      rates_3per2_bwd[k] = triplet_bids[1]
      rates_1per2_bwd[k] = triplet_asks[0]
      rates_3per1_bwd[k] = ask_31

      k += 1
      ## next, mid_profit
      rates_1per2_fwd[k] = 0.5*(triplet_bids[0] + triplet_asks[0])
      rates_3per2_fwd[k] = 0.5*(triplet_asks[1] + triplet_bids[1])
      rates_3per1_fwd[k] = 0.5*(bid_31 + ask_31)
      rates_1per2_bwd[k] = 0.5*(triplet_bids[0] + triplet_asks[0])
      rates_3per2_bwd[k] = 0.5*(triplet_asks[1] + triplet_bids[1])
      rates_3per1_bwd[k] = 0.5*(bid_31 + ask_31)

      k += 1
      ## 1st instant, 2nd mid_profit, 3rd max_profit
      rates_1per2_fwd[k] = triplet_asks[0]
      rates_3per2_fwd[k] = 0.5*(triplet_bids[1] + triplet_asks[1])
      rates_3per1_fwd[k] = bid_31
      rates_3per2_bwd[k] = triplet_asks[1]
      rates_1per2_bwd[k] = 0.5*(triplet_bids[0] + triplet_asks[0])
      rates_3per1_bwd[k] = ask_31

      k += 1
      ## 1st instant, 2nd mid_profit, 3rd max+0.01% profit
      rates_1per2_fwd[k] = triplet_asks[0]
      rates_3per2_fwd[k] = 0.5*(triplet_bids[1] + triplet_asks[1])
      rates_3per1_fwd[k] = (1.0 - 0.0001)*bid_31
      rates_3per2_bwd[k] = triplet_asks[1]
      rates_1per2_bwd[k] = 0.5*(triplet_bids[0] + triplet_asks[0])
      rates_3per1_bwd[k] = 1.0001*ask_31

      k += 1
      ## 1st&2nd instant, 3rd max_profit
      rates_1per2_fwd[k] = triplet_asks[0]
      rates_3per2_fwd[k] = triplet_bids[1]
      rates_3per1_fwd[k] = bid_31
      rates_3per2_bwd[k] = triplet_asks[1]
      rates_1per2_bwd[k] = triplet_bids[0]
      rates_3per1_bwd[k] = ask_31

      k += 1
      ## last, instant
      rates_1per2_fwd[k] = triplet_asks[0]
      rates_3per2_fwd[k] = triplet_bids[1]
      rates_3per1_fwd[k] = ask_31
      rates_3per2_bwd[k] = triplet_asks[1]
      rates_1per2_bwd[k] = triplet_bids[0]
      rates_3per1_bwd[k] = bid_31

      for j in range(len(self.arb_names)):
        profit_fwd = self.get_arbitrage_profit_fwd(rates_1per2_fwd[j],
                               rates_3per2_fwd[j], rates_3per1_fwd[j])
        profit_bwd = self.get_arbitrage_profit_bwd(rates_1per2_bwd[j], 
                               rates_3per2_bwd[j], rates_3per1_bwd[j])
        if 100*profit_fwd > 0.85:
          the_triplets[j].append(triplet_fwd)
          the_profits[ j].append( profit_fwd)
          the_rates[   j].append([rates_1per2_fwd[j], 
              rates_3per2_fwd[j], rates_3per1_fwd[j]])
          if j >= (len(self.arb_names) - 2):
            print("profitbale fwd triplet for ", self.arb_names[j], " strategy")
            print(triplet_fwd, 100*profit_fwd, "%")
          # end if
        # end if
        if 100*profit_bwd > 0.85:
          the_triplets[j].append(triplet_bwd)
          the_profits[ j].append( profit_bwd)
          the_rates[   j].append([rates_3per2_bwd[j], 
              rates_1per2_bwd[j], rates_3per1_bwd[j]])
          if j >= (len(self.arb_names) - 2):
            print("profitbale bwd triplet for ", self.arb_names[j], " strategy")
            print(triplet_bwd, 100*profit_bwd, "%")
        # end if
      # end for j
    # end for triplets

    for i in range(len(self.arb_names)):
      the_triplets[i] = np.array(the_triplets[i])
      the_profits[ i] = np.array(the_profits[ i])
      the_rates[   i] = np.array(the_rates[   i])

      ind = np.argsort(the_profits[i])
      the_triplets[i] = the_triplets[i][ind]
      the_profits[ i] = the_profits[ i][ind]
      the_rates[   i] = the_rates[   i][ind]
    # end for i

    self.arb_triplets = the_triplets
    self.arb_profits  = the_profits
    self.arb_rates    = the_rates
  # end get_best_arbitrage

  def display_best_arbitrage(self):
    self.get_best_arbitrage()
    for i in range(len(self.arb_names)):
      if len(self.arb_triplets[i]) > 0:
        print("Top " + self.arb_names[i] + " profit for " + \
self.arb_triplets[i][-1] + ": ", 100*self.arb_profits[i][-1], " %")
      # end if
    # end for i
  # end display_best_arbitrage

  def get_triplet_balances(self, triplet):
    self.get_balances()
    balances = np.zeros(3)
    for i, name in enumerate(triplet.split("-")):
      if name not in self.currencies.keys():
        balances[i] = 0.0
      else:
        balances[i] = self.currencies[name]["balance"]
      # end if/else
    # end for i
    return balances
  # end get_triplet_balances

  def limit_buy(self, market, rate, quantity):
    url = self.base_url + "/market/buylimit?" + self.end_url_limit + \
          "&market=" + market + "&quantity=" + str(quantity) + "&rate=" \
        + str(rate)
    print()
    print(url)
    result = self._get(url)

    return result
  # end limit_buy

  def limit_sell(self, market, rate, quantity):
    url = self.base_url + "/market/selllimit?" + self.end_url_limit + \
          "&market=" + market + "&quantity=" + str(quantity) + "&rate=" \
        + str(rate)
    print()
    print(url)
    result = self._get(url)

    return result
  # end limit_sell

  def perform_best_arbitrage(self, name=""):
    self.need_speed = True
    cur_time = str(datetime.datetime.now())
    tmades = np.zeros(3)
    tfills = np.zeros(3)

    self.get_best_arbitrage()
    t0 = time.time()

    if name != "":
      if name not in self.arb_names:
        print("Error! Input 'name' not in self.arb_names")
        sys.exit()
      # end if
      arb_names = np.array(self.arb_names)
      ind = np.where(name == arb_names)[0][0]

      if len(self.arb_triplets[ind]) == 0:
        return
      # end if
    else:
      for i in range(len(self.arb_names)):
        if len(self.arb_triplets[i]) > 0:
          ind = i
        # end if/else
      # end for i
    # end if/else

    arb_name = self.arb_names[ind]
    os.chdir("arb_" + arb_name)
    fname = "arbitrage_" + cur_time
    with open(fname, "a") as fid:
      fid.write("\nPerforming " + arb_name + " arbitrage")
    # end with
    triplet = self.arb_triplets[ind][-1]
    profit  = self.arb_profits[ ind][-1]
    rates   = self.arb_rates[   ind][-1]

    balances0 = self.get_triplet_balances(triplet)
    balances1 = balances0.copy()

    print("triplet: ", triplet)
    print("Expected trade percent profit: ", 100*profit)
    print("Initial balances: ", balances0)
    with open(fname, "a") as fid:
      fid.write("\ntriplet: " + triplet)
      fid.write("\nExpected trade percent profit: " + str(100*profit))
      to_print = "".join(str(val) + "\t" for val in balances0)
      fid.write("\nInitial balances: " + to_print)
    # end with open

    orders  = ["","",""]
    markets = []
    triplet0, triplet1, triplet2 = triplet.split("-")
    markets.append(triplet0 + "-" + triplet1)
    markets.append(triplet2 + "-" + triplet1)

    value = self.value
    if   triplet0 != "BTC":
      value /= rates[2]
      orders[2] = "buy"
      markets.append(triplet2 + "-" + triplet0)
    elif triplet2 != "BTC":
      orders[2] = "sell"
      markets.append(triplet0 + "-" + triplet2)
    else:
      print("Trying to perform_best_arbitrage on")
      print("non BTC,ETH triplet, crashing now.")
      print("triplet: ", triplet)
      sys.exit()
    # end if/elif/else

    if balances0[0] < value:
      print("Insufficient funds!")
      print("current {0}: {1}".format(triplet0, balances[0]))
      print("needed {0}: {1}".format( triplet0, value))
      with open(fname, "a") as fid:
        fid.write("\nInsufficient funds!")
        fid.write("\ncurrent {0}: {1}".format(triplet0, balances[0]))
        fid.write("\nneeded {0}: {1}".format( triplet0, value))
      # end with
      return
    # end if

    quantity = np.around(value / rates[0], decimals=8)
    quantity2 = 0.9975*quantity*rates[1]
    if triplet0 == "ETH":
      quantity2 /= 1.0025
      quantity2 /= rates[2]
    # end if
    
    ## truncate
    parts = str(quantity2).split(".")
    quantity2 = float("".join(parts[0] + "." + parts[1][:8]))

    quantities = []
    quantities.append(quantity)
    quantities.append(quantity)
    quantities.append(quantity2)

    uuids = ["","",""]
    to_print1 = "".join(str(val) + "\t" for val in    markets)
    to_print2 = "".join(str(val) + "\t" for val in      rates)
    to_print3 = "".join(str(val) + "\t" for val in quantities)
    with open(fname, "a") as fid:
      fid.write("\nmarkets: "    + to_print1)
      fid.write("\nrates: "      + to_print2)
      fid.write("\nquantities: " + to_print3)
    # end with
    print("markets: ", markets)
    print("rates: ", rates)
    print("quantities: ", quantities)

    uuids[0] = self.limit_buy(markets[0], rates[0], quantities[0])["uuid"]
    #uuids[0] = "9635da72-fdc2-41d3-8631-35727f9db1e4"
    orders[0] = "made"
    tmades[0] = time.time()
    with open(fname, "a") as fid:
      fid.write("\nuuids[0]: " + uuids[0])
      to_print = "".join(str(val) + "\t" for val in orders)
      fid.write("\norders before while: " + to_print)
      fid.close()
    # end with
    os.chdir("..")
    cnt = 0
    while (len(set(orders)) != 1) or (orders[1] != "filled"):
      os.chdir("arb_" + arb_name)
      with open(fname, "a") as fid:
        to_print = "".join(str(val) + "\t" for val in orders)
        fid.write("\norders: " + to_print)
      # end with

      balances = self.get_triplet_balances(triplet)
      
      if (orders[1] == "") and ((balances[1] - quantities[1]) > -9e-9):
        with open(fname, "a") as fid:
          fid.write("\nmaking order for 23")
        # end with
        orders[1] = "made"
        uuids[1] = self.limit_sell(markets[1], rates[1], \
                     quantities[1])["uuid"]
        #uuids[1] = "9635da72-fdc2-41d3-8631-35727f9db1e4"
        tmades[1] = time.time()
        with open(fname, "a") as fid:
          fid.write("\nuuids[1]: " + uuids[0])
        # end with
      # end if
      if   orders[2] == "buy":
        if ((balances[0] - quantities[2]*rates[2]) > -9e-9):
          with open(fname, "a") as fid:
            fid.write("\nmaking buy order for 31")
          # end with
          orders[2] = "made"
          uuids[2] = self.limit_buy(markets[2], rates[2], \
                       quantities[2])["uuid"]
          #uuids[2] = "9635da72-fdc2-41d3-8631-35727f9db1e4"
          tmades[2] = time.time()
          with open(fname, "a") as fid:
            fid.write("\nuuids[2]: " + uuids[2])
          # end with
        # end if
      elif orders[2] == "sell":
        if ((balances[2] - quantities[2]) > -9e-9):
          with open(fname, "a") as fid:
            fid.write("\nmaking sell order for 31")
          # end with
          orders[2] = "made"
          uuids[2] = self.limit_sell(markets[2], rates[2], \
                       quantities[2])["uuid"]
          #uuids[2] = "9635da72-fdc2-41d3-8631-35727f9db1e4"
          tmades[2] = time.time()
          with open(fname, "a") as fid:
            fid.write("\nuuids[2]: " + uuids[2])
          # end with
        # end if
      # end if/elif
      os.chdir("..")

      ## check open orders
      uuids = np.array(uuids)
      inds = np.where(uuids != "")[0]
      for ind in inds:
        url = self.base_url + "/account/getorder?" + "uuid=" + \
              uuids[ind] + "&" + self.end_url_view
        result = self._get(url)

        os.chdir("uuids")
        fname_uuid = "uuid_" + str(uuids[ind]) + ".txt"
        with open(fname_uuid, "w") as fid:
          fid.write(json.dumps(result))
          fid.write("\n")
        # end with
        os.chdir("..")

        if result["IsOpen"] == False:
          if orders[ind] != "filled":
            orders[ind] = "filled"
            tfills[ind] = time.time()
            print("orders: ", orders)

            rate        = result["Limit"]
            quantity    = result["Quantity"]
            price       = result["Price"]
            commishPaid = result["CommissionPaid"]

            if   ind == 0:
              balances1[0]  = balances1[0] - price - commishPaid
              balances1[1] += quantity
            elif ind == 1:
              balances1[2]  = balances1[2] + price - commishPaid
              balances1[1] -= quantity
            elif ind == 2:
              if   result["Type"] == "LIMIT_BUY":
                balances1[0] += quantity
                balances1[2]  = balances1[2] - price - commishPaid
              elif result["Type"] == "LIMIT_SELL":
                balances1[2] -= quantity
                balances1[0]  = balances1[0] + price - commishPaid
              # end if/elif
            # end if/elifs
          # end if
        # end if
      # end for
      uuids  = uuids.tolist()
      if "" not in orders:
        self.need_speed = False
      # end if
    # end while
    final_value = value + (balances1[0] - balances0[0])
    
    total_profit = 100*(balances1 - balances0) / balances0
    trade_profit = 100*(final_value - value) / value
    tf = time.time()

    print("Initial Balances: ", balances0)
    print("Final   Balances: ", balances1)
    print("Balance Percent Profit: ", total_profit)
    print("Initial Value: ", value)
    print("Final Value: ", final_value)
    print("Trade Percent Profit: ", trade_profit)
    print("Time from made to fill: ", (tfills - tmades))
    print("Time to fill: ", (tfills - t0))
    print("Total Elapsed Time (in seconds): ", (tf - t0))

    os.chdir("arb_" + arb_name)
    to_print1 = "".join(str(val) + "\t" for val in balances0)
    to_print2 = "".join(str(val) + "\t" for val in balances1)
    to_print3 = "".join(str(val) + "\t" for val in total_profit )
    to_print4 = "".join(str(val) + "\t" for val in (tfills - tmades))
    to_print5 = "".join(str(val) + "\t" for val in (tfills - t0))
    with open(fname, "a") as fid:
      fid.write("\nInitial Balances: "           + to_print1)
      fid.write("\nFinal   Balances: "           + to_print2)
      fid.write("\nBalance Percent Profit: "     + to_print3)
      fid.write("\nInitial Value: "              + str(value))
      fid.write("\nFinal   Value: "              + str(final_value))
      fid.write("\nTrade Percent Profit: "       + str(trade_profit))
      fid.write("\nTime from made to fill (s): " + to_print4)
      fid.write("\nTime to fill (s): "           + to_print5)
      fid.write("\nElapsed Time (in seconds): " + str(tf - t0))
    # end with
    os.chdir("..")
    self.best_arbs_cnt += 1
  # end perform_best_arbitrage

  def finish_order(self):
    triplet = "ETH-DNT-BTC"
    market = "BTC-DNT"
    rate = 1.465e-5
    quantity = 145.8491182
 
    cnt = 0
    while True:
      cnt += 1; print(cnt)
      balances = self.get_triplet_balances(triplet)
      if ((balances[1] - quantity) > -9e-9):
        uuid = self.limit_sell(market, rate, quantity)["uuid"]
        print(uuid)
        return
      # end if
      time.sleep(0.25)
    # end while
  # end finish_order
# end bittrex
## end bittrex.py
