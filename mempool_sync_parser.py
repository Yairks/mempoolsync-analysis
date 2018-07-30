# Created by Yair Kosowsky-Sachs to analyze mempoolsync() data.
# Designed to parse the falafel008 and falafel009 received files for two days of info.
# This will determine how many UTXO in mempoolsync() were not
# already part of the receiver's mempool and how many of the new ones made it into
# the next block.

# Housekeeping notes:
# 1) The path to the files MUST be
# "~/MempoolSyncAnalysis/[MM-DD-YY]/falafel00[X]/expLogFiles/received/".
# Alternatively, just change it. However, make sure to replace all file names (it appears in several place).
# The program will prompt you for the home directory the first time you use it.
# 2) Do NOT use the folder 06-26-18. It has a weird format for its stuff (thanks, Anas). Better to delete it.
# 3) Requirements: install (via pip) xlwt and python-bitcoinlib

import xlwt
import os
import bitcoin.rpc


def analyze_falafel(path, falafel_number):
	"""Most falafels are brownish and formed in balls.
	The point of this method is to determine any unusual
	characteristics in a given falafel.

	This method looks at the data outputted by a particular
	falafel node on a particular day and determines which
	transactions in each mempoolsync() call were redundant
	(the node already had them), which were new (the node
	didn't already have them), and which of those new
	transactions actually made it into a block (this is
	called "new and used")."""

	# tx_list will hold the old, new, and new_and_used data for each mempoolsync call
	tx_list = list()

	# These bad boys are just for some fun and quick data analysis. Not strictly necessary.
	total_old_tx = total_new_tx = total_new_and_used_tx = 0

	# Run through each "x_before_mempoolFile.txt"
	num_files = int(len([name for name in os.listdir(path + "/received/")]) / 3)
	for x in range(num_files):
		if x % 10 == 0:
			print("Looking through file " + str(x))
			print(
				"Current totals for this node -- old: " +
				str(total_old_tx) +
				" new: " +
				str(total_new_tx) +
				" new/used: " +
				str(total_new_and_used_tx) +
				"\n")

		# File with receiver node's mempool transactions before receiving a given mempoolsync() call
		with open(path + "/received/" + str(x) + "_before_mempoolFile.txt") as f:
			mempool = f.read()

		# File that stores the transactions in a mempoolsync() call
		with open(path + "/received/" + str(x) + "_vecFile_invreceived.txt") as f:
			txids = f.readlines()

		# Log file
		with open(path + "/logNode_falafel00" + str(falafel_number) + ".txt") as f:
			logs = f.read()

		old_tx = new_tx = new_and_used_tx = 0

		# Check for overlap of the mempoolsync() and the receiver's mempool
		for txid in txids:
			# First couple of lines aren't transactions. Skip them.
			if txid.find("tx") == -1 or txid.find("fa1afe1") != -1:
				continue

			# If the mempool already has the transaction, it's redundant
			if mempool.find(txid[3:67]) != -1:
				old_tx += 1

			# We have a new transaction!
			else:
				new_tx += 1

				# Check if the transaction made it into a later block
				try:
					proxy.getrawtransaction(bytes.fromhex(reverse(txid[3:67])))
					# We did it!
					new_and_used_tx += 1

				# If the proxy can't find the transaction (because it didn't
				# make it into a block), it will throw an error.
				except IndexError:
					continue
					# Nothing to see here, folks

		# Store the data for this mempoolsync() call
		tx_list.append((old_tx, new_tx, new_and_used_tx))

		total_old_tx += old_tx
		total_new_tx += new_tx
		total_new_and_used_tx += new_and_used_tx

	print("\n\nIn total, " + str(total_old_tx) + " were repeat transactions and ", end="")
	print(str(total_new_tx) + " were new transactions.")
	print("Out of the new transactions, " + str(total_new_and_used_tx), end=" ")
	print("were used in a later block.")

	return tx_list


def reverse(old_hash):
	"""The log file gives me little endian hashes which I need
	to reverse to big endian to satisfy the all-powerful and
	never-satisfied bitcoin rpc. ALL HAIL BITCOIN CORE!

	This method will flip the bytes from one endianness to another.

	Needed both for block hashes AND transaction IDs."""

	new_hash = ""
	for x in range(0, len(old_hash), 2):

		new_hash = str(old_hash[x]) + str(old_hash[x + 1]) + str(new_hash)

	return new_hash


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

PATH = home_dir + "/MempoolSyncAnalysis"

# Random initializers for bitcoin RPC and for spreadsheet writer.
print("\nTrying to create Bitcoin proxy.", end=" ")
proxy = bitcoin.rpc.Proxy()
print("Success!")
print("Trying to create a spreadsheet.", end=" ")
wb = xlwt.Workbook()
ws = wb.add_sheet("txes")
print("Success!")

# For every node of every day, find the redundant, new, and new-and-made-it-into-next-block transactions.
# Also, record the data from each mempoolsync call in a spreadsheet.
date = node = 0
for date_folder in os.listdir(PATH):
	# Skip weird hidden files
	if date_folder.find(".") == 0:
		continue

	# Check that the directory is happy
	try:
		mempool_files = os.listdir(PATH + "/" + date_folder)
	except NotADirectoryError:
		print("Couldn't find the directory " + PATH + "/" + date_folder)
		print("If you're including data from 06-26-18, then because Anas used a ")
		print("weird format for that day. Delete that folder and try again.")
		break

	for node_folder in mempool_files:
		# Skip weird hidden files
		if node_folder.find(".") == 0:
			continue

		tx_list = analyze_falafel(PATH + "/" + date_folder + "/" + node_folder, node_folder[9])

		# Recording data. I'm such a cool scientist.
		ws.write(0, 6 * node + 3 * date, "Redundant tx - falafel00" + str(node + 8) + " 06/2" + str(date + 7) + "/18")
		ws.write(0, 6 * node + 3 * date + 1, "New tx - falafel00" + str(node + 8) + " 06/2" + str(date + 7) + "/18")
		ws.write(0, 6 * node + 3 * date + 2, "New and Used tx")
		for i, row in enumerate(tuple(tx_list)):
			for j, col in enumerate(row):
				ws.write(i + 1, j + 6 * node + 3 * date, col)

		print("Data recorded.\n")
		node += 1
	date += 1

	# Reset node value so we don't get weird falafel0010's or anything
	node = 0

print("Saving to spreadsheet", end=" ")
wb.save("tx_info.xls")
print("You did it! Congrats.")
# Sweet.
