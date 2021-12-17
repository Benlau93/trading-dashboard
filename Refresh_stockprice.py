# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 20:47:15 2020

@author: ben_l
"""

# This script get updated stock price from yahoo finance

import pandas as pd
import yfinance as yf
from datetime import date

def main():
    df = pd.read_excel("Transaction Data.xlsx",sheet_name=None)
    data = df["Data"]
    open_ = df["Open Position"]
    closed = df["Closed Position"]
    # convert datetime
    open_["Date"] = pd.to_datetime(open_["Date"],format ="%Y-%m-%d")
    
    for sym in open_["Symbol"].unique():
        idx = open_[open_["Symbol"]==sym].index[0]
        curr = open_.loc[idx,"Currency"]
        if curr =="SGD":
            ticker = sym + ".SI"
        else:
            ticker = sym
            
        # get stock price
        history = yf.download(tickers=ticker,period="3d")
        open_.loc[idx,"Previous Close"] = history["Close"].iloc[-1]
        open_.loc[idx,"% Change"] = ((history["Close"].iloc[-1] - history["Close"].iloc[-2])/history["Close"].iloc[-2])
        open_.loc[idx,"Change"] = history["Close"].iloc[-1] - history["Close"].iloc[-2]
    
    	# get current P/L
        open_.loc[idx,"P/L (Origin Currency)"] = round((history["Close"].iloc[-1] * open_.loc[idx,"Shares"])  - (open_.loc[idx,"Avg Price"] * open_.loc[idx,"Shares"] + open_.loc[idx,"Comm"]),2)
    
        if curr !="SGD":
            open_.loc[idx,"P/L (SGD)"] = round(((history["Close"].iloc[-1] * open_.loc[idx,"Shares"]) * (open_.loc[idx,"Exchange Rate"] * 0.99)) - open_.loc[idx,"Amount (SGD)"],2) # 1% spread in currency conversion
        else:
            open_.loc[idx,"P/L (SGD)"] = round(open_.loc[idx,"P/L (Origin Currency)"],2)
    	    
        open_.loc[idx,"P/L (%)"] = open_.loc[idx,"P/L (Origin Currency)"] / open_.loc[idx,"Amount"]
        
        # generate current value of stock
        open_.loc[idx,"Value (SGD)"] = open_.loc[idx,"Previous Close"] * open_.loc[idx,"Shares"] * open_.loc[idx,"Exchange Rate"] * 0.99
        
        print("Sucessfully update price for {}".format(sym))

        # get number of holdings
        open_.loc[idx,"Holdings (days)"] = (pd.to_datetime(date.today()) - open_.loc[idx,"Date"]).days
    


    # generate new weightage
    open_["Weightage"] = open_["Value (SGD)"] / open_["Value (SGD)"].sum()
    
    # write to excel
    with pd.ExcelWriter("Transaction Data.xlsx",
    	                    date_format="DD-MMM-YY",
    	                    datetime_format = "DD-MMM-YY") as writer:
        data.to_excel(writer,sheet_name="Data",index=False)
        closed.to_excel(writer,sheet_name="Closed Position",index=False)
        open_.to_excel(writer,sheet_name="Open Position",index=False)
        
if __name__== "__main__":
  main()

