# -*- coding: utf-8 -*-
"""
Created on Sun Oct 25 09:48:32 2015

@author: Maxim
"""
from datetime import datetime
import re

class GarminActivity(object):
    """
    Initialize with the raw json: activity = GarminActivity( json_dict )
    Getters access the json directly.
    06-11-2016: updated to activity search service 1.2 (e.g. capitalized parents)
    """
    ACTIVITY_SUMMARY_KEY = 'activitySummary'
    
    def __init__( self, json_dict ):
        self.json_dict = json_dict
        self.json_summary = json_dict['activitySummary']

    def getID( self ):
        return int( self.json_dict['activityId'] )

    def getName( self ):
        return self.json_dict['activityName']
        
    def getCategory( self ):
        """ The 'general' type of an activity, disregarding the subtype. e.g. running, cycling, swimming, hiking... """
        return self.json_dict['activityType']['parent']['key']
    
    def isRun( self ):
        if self.getCategory() == 'running':
            return True
        else:
            return False
    
    def getDistance( self ):
        parent = self.json_summary['SumDistance']
        
        unit = parent['uom']
        if unit != 'kilometer':
            raise Exception("Distance has the wrong unit: '%s'" % unit)
        
        return float( parent['value'] )
    
    def getDuration( self ):
        parent = self.json_summary['SumDuration'] 
    
        unit = parent['uom']
        if unit != 'second':
            raise Exception("Time has the wrong unit: '%s'" % unit)
        
        return float( parent['value'] )
        
    def getComment( self ):
        comment = self.json_dict['activityDescription']
        # Replace any whitespace with a space to eliminate enters.
        return re.sub(r'\s', ' ', comment)
        
    def getDate( self ):
        """ Returns datetime object
            Note: this is in the GMT timezone !!!"""
        # First ten characters of timestamp
        date_yyyymmdd = self.json_summary['BeginTimestamp']['value']
        date = datetime.strptime(date_yyyymmdd,"%Y-%m-%dT%H:%M:%S.%fZ")
        return date
        
    def getStartTime( self ):
        """ Returns string 'hh:mm' for the correct timezone"""
        full_date = self.json_summary['BeginTimestamp']['display'] # 'Thu, 2015 Oct 22 17:19'
        match = re.search( r'\d{2}:\d{2}', full_date ) # Get the time hh:mm
        return match.group()
        
    def getBpmMax( self ):
        try:
            return float( self.json_summary['MaxHeartRate']['value'] ) 
        except KeyError:
            return None
    
    def getBpmAvg( self ):
        try:
            return float( self.json_summary['WeightedMeanHeartRate']['value'] ) 
        except KeyError:
            return None
            
    def getLatitude( self ):
        try:
            return float( self.json_summary['BeginLatitude']['value'] ) 
        except KeyError:
            return None        
    
    def getLongitude( self ):
        try:
            return float( self.json_summary['BeginLongitude']['value'] ) 
        except KeyError:
            return None
    
    def getTCX(self, handler):
        """ handler = GarminHandler object that is logged in to Garmin account"""
        if not handler:
            raise Exception("Tcx can only be downlaoded if GarminHandler object is given.")
        
        return handler.getFileDataByID( self.getID(), 'tcx' )    
    
    def getCSV(self, handler):
        """ handler = GarminHandler object that is logged in to Garmin account"""
        if not handler:
            raise Exception("Tcx can only be downlaoded if GarminHandler object is given.")
        
        return handler.getFileDataByID( self.getID(), 'csv' )
        
    def getGPX(self, handler):
        """ handler = GarminHandler object that is logged in to Garmin account"""
        if not handler:
            raise Exception("Tcx can only be downlaoded if GarminHandler object is given.")
        
        return handler.getFileDataByID( self.getID(), 'gpx' )
    
    