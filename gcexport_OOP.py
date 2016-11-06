#!/usr/bin/python

"""
File: gcexport.py
Author: Kyle Krafka (https://github.com/kjkjava/)
Date: April 28, 2015

Description:	Use this script to export your fitness data from Garmin Connect.
				See README.md for more information.
"""

import re
from urllib import urlencode
from datetime import datetime
from getpass import getpass
from sys import argv
from os.path import isdir
from os.path import isfile
from os import mkdir
from os import remove
from xml.dom.minidom import parseString

import urllib2, cookielib, json
from fileinput import filename

import argparse
import zipfile

from GarminHandler import GarminHandler

script_version = '1.0.0'
current_date = datetime.now().strftime('%Y-%m-%d')
activities_directory = './' + current_date + '_garmin_connect_export'

parser = argparse.ArgumentParser()

# TODO: Implement verbose and/or quiet options.
# parser.add_argument('-v', '--verbose', help="increase output verbosity", action="store_true")
parser.add_argument('--version', help="print version and exit", action="store_true")
parser.add_argument('--username', help="your Garmin Connect username (otherwise, you will be prompted)", nargs='?')
parser.add_argument('--password', help="your Garmin Connect password (otherwise, you will be prompted)", nargs='?')

parser.add_argument('-c', '--count', nargs='?', default="1",
	help="number of recent activities to download, or 'all' (default: 1)")

parser.add_argument('-f', '--format', nargs='?', choices=['gpx', 'tcx', 'csv', 'original', 'none'], default="gpx",
	help="export format; can be 'gpx', 'tcx', 'csv', or 'original' (default: 'gpx'). Or 'none' if no file should be saved for each file")

parser.add_argument('-d', '--directory', nargs='?', default=activities_directory,
	help="the directory to export to (default: './YYYY-MM-DD_garmin_connect_export')")

parser.add_argument('-u', '--unzip',
	help="if downloading ZIP files (format: 'original'), unzip the file and removes the ZIP file",
	action="store_true")

parser.add_argument('-r', '--reverse',
	help="start with oldest activity (otherwise starts with newest)",
	action="store_true")
    
args = parser.parse_args()

if args.version:
	print argv[0] + ", version " + script_version
	exit(0)

# Convert the count to integer or empty if all.
if args.count == 'all': 
    total_to_download = None
else:
    total_to_download = int(args.count)

print 'Welcome to Garmin Connect Exporter!'

# Create directory for data files.
if isdir(args.directory):
	print 'Warning: Output directory already exists. Will skip already-downloaded files and append to the CSV file.'

username = args.username if args.username else raw_input('Username: ')
password = args.password if args.password else getpass()

# Login and initialize the handler. Raises exception if login failed.
garmin_handler = GarminHandler()
garmin_handler.login( username, password )

if not isdir(args.directory):
	mkdir(args.directory)

csv_filename = args.directory + '/activities.csv'
csv_existed = isfile(csv_filename)

csv_file = open(csv_filename, 'a')

# Write header to CSV file
if not csv_existed:
	csv_file.write('Activity ID,Activity Name,Description,Begin Timestamp,End Timestamp,Activity Type,Distance (km),Duration (s),Max. Heart Rate (bpm),Avg. Heart Rate (bpm),Begin Latitude (Decimal Degrees Raw),Begin Longitude (Decimal Degrees Raw)\n')

# Create generator for activities. Generates activities until specified number of activities are retrieved.
# Activity is a dictionary object of the json. (without the redundant first 'activity' key)
activities_generator = garmin_handler.getActivities( limit = total_to_download, reversed = args.reverse )

for activity in activities_generator:
    # Display which entry we're working on.
    print 'Garmin Connect activity: [%d] %s' % ( activity.getID(), activity.getName() ),
    print '\t %s, %d, %d km' % ( activity.getDate(), activity.getDuration(), activity.getDistance() )
    
    # Download the data file from Garmin Connect.
    # If the download fails (e.g., due to timeout), this script will die, but nothing
    # will have been written to disk about this activity, so just running it again
    # should pick up where it left off.
    if args.format != 'none': # 17-02-2016: able to skip downloading file
        print '\tDownloading file...'
        data = garmin_handler.getFileDataByID( activity.getID(), args.format )
        
        if args.format == 'original':
            data_filename = "%s/activity_%s.%s" % (args.directory, activity.getID(), 'zip')
            fit_filename = args.directory + '/' + activity.getID() + '.fit'
            file_mode = 'wb'
        else:
            data_filename = "%s/activity_%s.%s" % (args.directory, activity.getID(), args.format)
            file_mode = 'w'

        if isfile(data_filename):
            print '\tData file already exists; skipping...'
            continue
        if args.format == 'original' and isfile(fit_filename):  # Regardless of unzip setting, don't redownload if the ZIP or FIT file exists.
            print '\tFIT data file already exists; skipping...'
            continue

        save_file = open(data_filename, file_mode)
        save_file.write(data)
        save_file.close()

    # Write stats to CSV.    
    csv_record = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
            activity.getID(),
            activity.getName(),
            activity.getComment(),
            activity.getDate(), #datetime object
            activity.getEndDate(),
            activity.getCategory(),
            activity.getDistance(),
            activity.getDuration(),
            activity.getBpmMax(),
            activity.getBpmAvg(),
            activity.getLatitude(),
            activity.getLongitude()
        )

    csv_file.write(csv_record.encode('utf8'))
    
    # Validate data. 
    if args.format == 'gpx':
        # Validate GPX data. If we have an activity without GPS data (e.g., running on a treadmill),
        # Garmin Connect still kicks out a GPX, but there is only activity information, no GPS data.
        # N.B. You can omit the XML parse (and the associated log messages) to speed things up.
        gpx = parseString(data)
        gpx_data_exists = len(gpx.getElementsByTagName('trkpt')) > 0

        if gpx_data_exists:
            print 'Done. GPX data saved.'
        else:
            print 'Done. No track points found.'
    elif args.format == 'original':
        if args.unzip and data_filename[-3:].lower() == 'zip':  # Even manual upload of a GPX file is zipped, but we'll validate the extension.
            print "Unzipping and removing original files...",
            zip_file = open(data_filename, 'rb')
            z = zipfile.ZipFile(zip_file)
            for name in z.namelist():
                z.extract(name, args.directory)
            zip_file.close()
            remove(data_filename)
        print 'Done.'
    else:
        # TODO: Consider validating other formats.
        print 'Done.'
         
csv_file.close()

print 'Done!'
