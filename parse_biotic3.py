# parse_biotic3.py
# Author: André Moan
# Written for python3

### DESCRIPTION
# This script takes XML files in the biotic v3.0 format, extracts a set of data fields
# (as specified below, see "vars") and writes that data out in a CSV long format.

# Used to parse biotic data from the IMR reference fleet.
# Biotic 3 reference: https://confluence.imr.no/display/API/Biotic+V3+API+documentation

# This script easily handles large multi-gigabyte sized XML files, because it uses the python
# SAX implementation that only keeps smaller chunks of the file in memory at any given time.

### EXAMPLE USAGE
# python3 parse_biotic3.py
# Running the script like this, without any additional parameters, makes it process all
# XML files in the current working directory.

# python3 parse_biotic3.py /home/andremoan/biotic/
# In this case, we've explicitly specified in which folder the script should look for the XML
# files.

### DETAILS
#  *  CSV file names are generated from the input filenames by replacing the XML file extension
#     with ".csv". If the input file names do not contain the XML file extension, then the string
#     ".csv" will be appended to the end of the filename.

#  *  The script minimally requires that a catch entry for a fishing station has at least the
#     following fields: a serial and a species name and either count or weight (or both).

#  *  Semicolons in station comments are replaced with regular colons, because the semicolon is
#     used as a delimeter in the output CSV files.
#
#  *  The string "NA" is inserted in place of missing values.

### OPTIONS

# Pattern to match against the names of all the files in the search path. Only filenames that match
# will be processed by the script.
NAME_PATTERN = "biotic*.xml"

# Biotic3 year files can contain many different mission types. Only data from missions of the type
# specified here will be extracted.
MISSIONTYPENAME = "Referanseflåten-Kyst"

# List of XML elements that correspond to the data fields that we're intested in. Note that this does not capture
# data that is stored as attributes of other elements, except in the case of the 'serial' field, which is handled
# in a special case. The order with which strings appear in this list also determines the column order in the CSV.
VARS = [
	"platformname", "callsignal", "serial", "stationstartdate", "stationstopdate", "latitudestart", "longitudestart",
	"area", "location", "fishingdepthmax", "fishingdepthmin", "gear", "gearcount", "soaktime", "stationcomment",
	"commonname", "catchweight", "catchcount", "lengthsampleweight", "lengthsamplecount", "specimensamplecount"]

# For slow computers; print a life sign to the console for every LIFESIGN hauls processed. 
# Set to 0 to disable.
LIFESIGN = 0

### Do not edit below this line

import xml.sax
import glob
import os
import sys

class Biotic3 (xml.sax.ContentHandler):
	def __init__(self, missiontypename, filename):
		self.missiontypename = missiontypename
		self.filename = filename
		self.vars = vars

		self.counter = [0, 0]
		self.parse = False
		self.data = None
		self.tag = ""
		self.parent = ""
		self.skipped = 0

		self.fob = open(filename, "w")
		self.fob.write('%s\n' % ';'.join([str(field) for field in VARS]).strip())

	def startElement(self, tag, attributes):
		self.parent = self.tag
		self.tag = tag
		if self.parse == True and self.tag == "fishstation":
			self.data["serial"] = attributes["serialnumber"]
			self.counter[0] = self.counter[0] + 1
			if (LIFESIGN > 0 and self.counter[0] % LIFESIGN == 0):
				print("-processed %d hauls with %d catch items" % (self.counter[0], self.counter[1]))
		
	def endElement(self, tag):

		if self.parse == True:

			if tag == "catchsample":
				self.counter[1] = self.counter[1] + self.append2csv()
				for var in ["catchweight", "catchcount", "lengthsamplecount","lengthsampleweight","specimensamplecount"]:
					if var in self.data:
						self.data.pop(var)

			if tag == "mission":
				self.data = None
				self.parse = False
		
			self.tag = ""

	def characters(self, content):
		content = content.replace("\n", "").strip()
		if self.parse == True and self.data is not None and self.tag in VARS:
			self.data[self.tag] = content

		if self.tag == "missiontypename" and content == self.missiontypename:
			self.parse = True
			self.data = {}

	def append2csv(self):

		if "serial" in self.data and "commonname" in self.data and ("catchweight" in self.data or "catchcount" in self.data or "lengthsamplecount" in self.data or "lengthsampleweight" in self.data or "specimensamplecount" in self.data):

			for var in VARS:
				if var not in self.data:
					self.data[var] = "NA"
			
			self.data["stationcomment"] = self.data["stationcomment"].replace(";", ":")
			
			output = []
				
			for var in VARS:
				output.append(self.data[var])
				
			output  = ';'.join([str(field) for field in output]).strip()
			self.fob.write(output + "\n")
			return 1
		self.skipped = self.skipped + 1
		return 0

	def endDocument(self):
		self.fob.close()
		print("Saved %d hauls with %d catch items (%d skipped due to missing data) in %s " % (self.counter[0], self.counter[1], self.skipped, self.filename))


if len(sys.argv) == 1:
	path = os.getcwd()
	print("No search path specified, assuming working directory.")
else:
	path = sys.argv[1]
	print("Search path set to: %s" % path)

files = sorted(glob.glob(path + "/" + NAME_PATTERN))

if len(files) == 0:
	print("No XML files found, please check search path.")
	exit()

print("Found %d data files, starting processing with LIFESIGN=%d." % (len(files), LIFESIGN))

parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces, 0)

for file in files:
	file_in = os.path.basename(file)
	file_out = file.replace(".xml", ".csv")

	Handler = Biotic3(MISSIONTYPENAME, filename=file_out)
	parser.setContentHandler(Handler)
	parser.parse(file_in)

print("Finished!")

# year serial
# 2009	29131
# 2011	28251
# 2013	33895
# 2015	27323
#		