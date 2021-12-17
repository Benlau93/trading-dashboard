# This script is to add transactional stock entry into the trading dashboard

import pandas as pd
import numpy as np
from datetime import date
import yfinance as yf

def main():
	df = pd.read_excel("Transaction Data.xlsx",sheet_name=None)
	data = df["Data"]
	open_ = df["Open Position"]
	closed = df["Closed Position"]

	# get transaction data
	print("Enter Transaction in the following format:")
	print("DATE(DD-MM-YYYY) SYMBOL ACTION PRICE SHARES COMM EXCHANGE_RATE")
	input_list = input().split()
	print()

	# validate input
	try:
		date = pd.to_datetime(input_list[0],format="%d-%m-%Y")
		sym = input_list[1].upper()
		action = input_list[2].capitalize() 
		
		if input_list[2].capitalize() not in ["Buy","Sell"]:
			raise ValueError()
			
		price = float(input_list[3])
		shares = float(input_list[4])
		comm = float(input_list[5])
		exchange_rate = float(input_list[6])
		if action=="Buy":
			amount = (price*shares + comm)
		else:
			amount = (price*shares - comm)
		
		amount_sgd = amount * exchange_rate

	except:
		raise Exception("Invalid format, Please check your inputs")
	    
	# find stock
	if exchange_rate==1:
		ticker = sym+".SI"
	else:
		ticker = sym
		
	stock = yf.Ticker(ticker)

	# validation
	if len(stock.info) <5:
		raise Exception("Please ensure that the Ticker Symbol is correct")

	# concat stock to data
	stock_data = pd.Series({"Date":date,
	                           "Name":stock.info["shortName"],
	                           "Symbol":sym,
	                           "Type":stock.info["quoteType"],
	                           "Currency":stock.info["currency"],
	                           "Action":action,
	                           "Price":price,
	                           "Shares":shares,
	                           "Comm":comm,
	                           "Exchange Rate":exchange_rate,
	                           "Amount":amount,
	                           "Amount (SGD)":amount_sgd})

	# add sector and industry if stock is equity
	stock_data["Sector"],stock_data["Industry"] =np.nan, np.nan
	if stock_data["Type"] == "EQUITY":
		stock_data["Sector"] = stock.info["sector"]
		stock_data["Industry"] = stock.info["industry"]

	# append to main dataframe
	data = data.append(stock_data,sort=True,ignore_index=True)

	# verbose
	print("{} {} Shares of {} at ${}".format("Bought" if action=="Buy" else "Sold",shares,sym,price))

	# determine if its an new position or existing position
	if sym in open_["Symbol"].tolist():
	    # existing
	    
	    # get position
		existing = open_[open_["Symbol"]==sym].copy()
		idx = open_[open_["Symbol"]==sym].index
	    
	    # check if close or add on position
		if action == existing["Action"].iloc[0]:
			# add position
			new_shares = existing["Shares"].iloc[0] + shares
			avg_price = ((existing["Shares"].iloc[0] * existing["Avg Price"].iloc[0]) + (price * shares)) / new_shares
			new_comm = existing["Comm"].iloc[0] + comm
			new_er = ((existing["Shares"].iloc[0] * existing["Exchange Rate"].iloc[0]) + (exchange_rate * shares)) / new_shares
			
			# update open position
			open_.loc[idx,"Avg Price"] = avg_price
			open_.loc[idx,"Shares"] = new_shares
			open_.loc[idx,"Comm"] = new_comm
			open_.loc[idx,"Exchange Rate"] = new_er
			open_.loc[idx,"Amount (SGD)"] += amount_sgd
			open_.loc[idx,"Amount"] += amount
	        # verbose
			print("Increased {} to {} Shares with Average Price of ${}".format(sym,new_shares,round(avg_price,2)))
		else:
			# close position
			if shares > existing["Shares"].iloc[0]:
				print("Invalid transaction. Please ensure that you have sufficient shares of {} to close the position".format(sym))
			elif shares <= existing["Shares"].iloc[0]:
				# update open position
				new_shares = existing["Shares"].iloc[0] - shares
				if new_shares==0:
					# drop open position
					open_.drop(idx,inplace=True)
				else:
					open_.loc[idx,"Shares"] = new_shares
					open_.loc[idx,"Amount"] -= amount
					open_.loc[idx,"Amount (SGD)"] -= amount_sgd
				# verbose
				print("Closed {} Shares of {} at ${}".format(shares,sym,price))
				print("{} Shares of {} remaining".format(new_shares,sym))
				
				# add to closed position
				new_close = existing[["Date","Name","Symbol","Type","Currency","Sector","Industry",
										"Shares","Avg Price","Comm","Amount","Amount (SGD)"]].copy()
				# renaming of column
				new_close.rename({"Date":"Date_Open",
									"Avg Price":"Price_Open",
									"Comm":"Comm_Open",
									"Amount":"Amount_Open",
									"Amount (SGD)":"Amount (SGD)_Open"},axis=1,inplace=True)
				# add closing data
				new_close["Date_Close"] = date
				new_close["Price_Close"] = price
				new_close["Comm_Close"] = comm
				new_close["Amount (SGD)_Close"] = amount_sgd
				new_close["Amount_Close"] = amount
				
				# get holding period
				new_close["Holding (days)"] = (new_close["Date_Close"] - new_close["Date_Open"]).dt.days
				
				# get P/L
				new_close["P/L (Origin Currency)"] =  new_close["Amount_Close"] - new_close["Amount_Open"]
				new_close["P/L (SGD)"] = new_close["Amount (SGD)_Close"] - new_close["Amount (SGD)_Open"]
				new_close["P/L (%)"] = new_close["P/L (SGD)"] / new_close["Amount (SGD)_Open"]
				
				# add to closed position
				closed = closed.append(new_close,sort=True,ignore_index=True)
				
				# verbose
				print("Closed {} position with a P/L (SGD) of ${}".format(sym,round(new_close["P/L (SGD)"].iloc[0],2)))
	            
	else:
		# add new exiting position
		# rename price
		stock_data.rename({"Price":"Avg Price"},axis=1,inplace=True)
		
		# add number of holdings days
		stock_data["Holdings (days)"] = (pd.to_datetime(date.today()) - stock_data["Date"]).days
		# add to open position
		open_ = open_.append(stock_data,sort=True,ignore_index=True)
		idx = open_[open_["Symbol"]==sym].index
		
		# verbose
		print("Opened new position")

	# write to excel
	# rearrange columns
	data = data[["Date","Name","Symbol","Type","Currency","Sector","Industry","Action","Price",
	            "Shares","Comm","Exchange Rate","Amount","Amount (SGD)"]]
	closed = closed[["Name","Symbol","Type","Currency","Sector","Industry","Date_Open","Price_Open","Shares",
	                "Comm_Open","Amount_Open","Amount (SGD)_Open","Date_Close","Price_Close","Comm_Close","Amount_Close","Amount (SGD)_Close",
	                "Holding (days)","P/L (Origin Currency)","P/L (SGD)","P/L (%)"]]
	open_ = open_[["Date","Name","Symbol","Type","Currency","Sector","Industry","Action","Avg Price",
	              "Shares","Comm","Exchange Rate","Amount","Amount (SGD)","Holdings (days)","Weightage","Previous Close","% Change","Change","P/L (Origin Currency)",
	              "P/L (SGD)","P/L (%)","Value (SGD)"]]

	# write to excel
	with pd.ExcelWriter("Transaction Data.xlsx",
						date_format="DD-MMM-YY",
						datetime_format = "DD-MMM-YY") as writer:
		data.to_excel(writer,sheet_name="Data",index=False)
		closed.to_excel(writer,sheet_name="Closed Position",index=False)
		open_.to_excel(writer,sheet_name="Open Position",index=False)

if __name__== "__main__":
  main()
