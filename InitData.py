import requests 

import numpy as np
import scipy.stats as si

import datetime

def BSM_Price(S, K, T, r, sigma, putcall):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = (np.log(S / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    if putcall == 'C':
        result = (S * si.norm.cdf(d1, 0.0, 1.0) - K * np.exp(-r * T) * si.norm.cdf(d2, 0.0, 1.0))
    elif putcall == 'P':
        result = (K * np.exp(-r * T) * si.norm.cdf(-d2, 0.0, 1.0) - S * si.norm.cdf(-d1, 0.0, 1.0))
    return result

def BSM_IV(S, K, T, r, price, putcall):
    thisIV = 1
    dIV = 0.01
    thresholdPx = 0.001
    for i in range(20):
        thisPx = BSM_Price(S, K, T, r, thisIV, putcall)
        dPx = BSM_Price(S, K, T, r, thisIV + dIV, putcall) - thisPx
        thisIV = thisIV + (price - thisPx) / dPx * dIV
        if dPx <= thresholdPx:
            break
    return thisIV

def DateStrToInt(dateStr):
    return (datetime.datetime.strptime(dateStr + 'UTC08', '%d%b%y%Z%H') - datetime.datetime.utcnow()).total_seconds() / 86400

def GetOptionBook():
    urlOptionBook = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    jsonOptionBook = requests.get(url = urlOptionBook).json() 
    resultOptionBook = jsonOptionBook['result']
    for i in resultOptionBook:
        instrument_name = i['instrument_name']
        instrument_data = instrument_name.split("-")
        underlying = instrument_data[0]
        expiry = instrument_data[1]
        strike = float(instrument_data[2])
        putcall = instrument_data[3]
        TTM = DateStrToInt(expiry)/365.25
        underlying_price = float(i['underlying_price'])
        bid_price = i['bid_price']
        ask_price = i['ask_price']
        mid_price = i['mid_price']

        if bid_price==None:
            i['bid_IV'] = None
        else:
            i['bid_IV'] = BSM_IV(underlying_price,strike,TTM,0,float(bid_price)*underlying_price,putcall)

        if ask_price==None:
            i['ask_IV'] = None
        else:
            i['ask_IV'] = BSM_IV(underlying_price,strike,TTM,0,float(ask_price)*underlying_price,putcall)

        if mid_price==None:
            i['mid_IV'] = None
        else:
            i['mid_IV'] = BSM_IV(underlying_price,strike,TTM,0,float(mid_price)*underlying_price,putcall)
        #print(i['mid_IV'] )

    return resultOptionBook
    #print([i['instrument_name'] for i in resultOptionBook])

def GetOptionMeta():
    urlOptionBook = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    jsonOptionBook = requests.get(url = urlOptionBook).json() 
    resultOptionBook = jsonOptionBook['result']
    dictMeta = {'Strike':[],'Expiry':[]}
    for i in resultOptionBook:

        instrument_name = i['instrument_name']
        instrument_data = instrument_name.split("-")
        expiry = instrument_data[1]
        strike = float(instrument_data[2])
        if not strike in dictMeta['Strike']:
            dictMeta['Strike'].append(strike)
        if not expiry in dictMeta['Expiry']:
            dictMeta['Expiry'].append(expiry)
        if not strike in dictMeta:
            dictMeta[strike]=[]
        if not expiry in dictMeta:
            dictMeta[expiry]=[]
        if not strike in dictMeta[expiry]:
            dictMeta[expiry].append(strike)
        if not expiry in dictMeta[strike]:
            dictMeta[strike].append(expiry)
        dictMeta['Strike'].sort()
    return dictMeta

OptionMeta = GetOptionMeta()
OptionBook = GetOptionBook()

thisExpiry = "25SEP20"
thisStrikes = ["BTC-"+thisExpiry+"-"+str(int(i)) for i in sorted(OptionMeta[thisExpiry])]
for i in thisStrikes:
    thisPut = [item for item in OptionBook if item.get('instrument_name')==i+"-P"][0]
    thisCall = [item for item in OptionBook if item.get('instrument_name')==i+"-C"][0]
    print(i, thisPut['bid_IV'], thisCall['bid_IV'], thisPut['ask_IV'], thisCall['ask_IV'])
