# Created by Yair Kosowsky-Sachs
# The purpose of this program is to find if there are any marked
# differences between mempoolsync() transactions that are new
# and ones that are redundant. New ones have a spectacularly high
# rate of acceptance into new blocks (99.9%) and we'd like to
# isolate them.

# Program layout:
# for transactions:
#   find out where it is positioned in the file (highest tx fee are at the top)
#   mark that position in new_list or old_list
# find mean and quartiles of position of transactions in each list
# display results

# Requirements: pandas, xlwt

# This program will run only one node from one day (though that's still 650,000 data points, so don't worry).

import os
import pandas
import xlwt

# These guys find the average position of a new or redundant transaction
old_tx = list()
new_tx = list()
# This boy find the number of new transactions at a given position
new_tx_position = [0] * 1000

# This will prompt the user for the path of the data to analyze.
# If it's been done before, it'll just load the path from path.txt
with open("path.txt", "r+") as path_file:
	info = path_file.read()

	if info.find("/") == -1:
		# Make them tell me what the path to the files is.
		print("CAUTION: Make sure that your files are stored correctly. For this program to function properly, data must")
		print("Be stored like this: ~/MempoolSyncAnalysis/[MM-DD-YY]/falafel00[x]/received/.")
		print("Mempool files must be stored like: [X]_before_mempoolFile.txt")
		print("Log file must be stored (in falafel folder) under name: LogNode_falafel00[N].txt")

		home_dir = input("\nI don't have the directory. Please enter the home directory of MempoolSyncAnalysis: ")

		print("Saving to file: path.txt")
		path_file.write(home_dir)

	else:
		home_dir = info
		print("\nLoaded home directory from path.txt. Home directory of MempoolSyncAnalysis: " + home_dir)

PATH = home_dir + "/MempoolSyncAnalysis/06-28-18/falafel008_1_expLogFiles"

# Run through each "x_before_mempoolFile.txt"
num_files = int(len([name for name in os.listdir(PATH + "/received/")]) / 3)
for x in range(num_files):
	if x % 10 == 0:
		print("Looking through file " + str(x))

	# File with receiver node's mempool transactions before receiving a given mempoolsync() call
	with open(PATH + "/received/" + str(x) + "_before_mempoolFile.txt") as f:
		mempool = f.read()

	# File that stores the transactions in a mempoolsync() call
	with open(PATH + "/received/" + str(x) + "_vecFile_invreceived.txt") as f:
		txids = f.readlines()

	counter = 0
	# Check for overlap of the mempoolsync() and the receiver's mempool
	for txid in txids:
		# First couple of lines aren't transactions. Skip them.
		if txid.find("tx") == -1 or txid.find("fa1afe1") != -1:
			continue

		# If the mempool already has the transaction, it's redundant. Store its position in the mempoolsync()
		if mempool.find(txid[3:67]) != -1:
			old_tx.append(counter)

		# We have a new transaction!
		else:
			new_tx.append(counter)
			new_tx_position[counter] += 1

		counter += 1

old_tx_data = pandas.DataFrame(old_tx)
new_tx_data = pandas.DataFrame(new_tx)


print("\nAlrighty, we got us some data.")
print("Old data (1st quartile, mean, 3rd quartile):")
print(str(old_tx_data.quantile(0.25)[0].item()))
print(str(old_tx_data.quantile(0.5)[0].item()))
print(str(old_tx_data.quantile(0.75)[0].item()))

print("New data (1st quartile, mean, 3rd quartile):")
print(str(new_tx_data.quantile(0.25)[0].item()))
print(str(new_tx_data.quantile(0.5)[0].item()))
print(str(new_tx_data.quantile(0.75)[0].item()))

print("\nSaving data about positional likelihood to position_correlation.xls")

wb = xlwt.Workbook()
ws = wb.add_sheet("Transaction position data")

ws.write(0, 0, "Percentage of times tx was new")

# Divide the value by the number of files to find the percentage of times a position was useful for a transaction
for i, value in enumerate(tuple(new_tx_position)):
	ws.write(i + 1, 0, value / num_files)

wb.save("position_correlation.xls")
