#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re, os, sys
from xml.sax.saxutils import escape 
from downloadCommon import getSeqName
from xml.dom.minidom import parse, parseString
from OracleInterface import OracleDownloader
from ddlInterface import createDdlInterface, attribsToDict
from NamingConvention import *


__author__ = "Scott Kirkwood (scott_kirkwood at berlios.com)"
__keywords__ = ['XML', 'DML', 'SQL', 'Databases', 'Agile DB', 'ALTER', 'CREATE TABLE', 'GPL']
__licence__ = "GNU Public License (GPL)"
__url__ = 'http://xml2dml.berlios.de'


class DownloadXml:
    def __init__(self, downloader, options):
        self.db = downloader
        self.options = options
        dbms='oracle'
        self.ddlInterface = createDdlInterface(dbms)
        if 'tables' not in self.options:
            self.options['tables'] = []
        
    def downloadSchema(self, tableList = None, of = sys.stdout):
        tables = self.db.getTables(tableList = self.options['tables'])

        for strTableName in tables:
            curTable = {
                'name' : strTableName,
                'columns' : []
            }
            desc = self.db.getTableComment(strTableName)
            if desc:
                curTable['desc'] = escape(desc)
            
            if self.options == None or 'getindexes' not in self.options or self.options['getindexes'] == True:
                curTable['indexes'] = self.db.getTableIndexes(strTableName)

            
            pkMap = {}
            for index in curTable['indexes']:
                if index[3]: # If Primary key
                    for nIndex, colName in enumerate(index[1]):
                        pkMap[colName] = nIndex + 1
            
            if self.options == None or 'getrelations' not in self.options or self.options['getrelations'] == True:
                curTable['relations'] = self.db.getTableRelations(strTableName)

            for colRow in self.db.getTableColumns(strTableName):
                (strColumnName, type, attlen, precision, attnotnull, default, bAutoIncrement) = colRow
                strComment = self.db.getColumnComment(strTableName, strColumnName)
                curCol = {
                    'name' : str(strColumnName),
                    'type' : str(type),
                    'size' : attlen,
                    'precision' : precision if precision else '',
                    'default' : default if default else '',
                    'desc' : escape(strComment) if strComment else '',
                    'null' : 'no' if attnotnull else '',
                    'key' : pkMap[strColumnName] if strColumnName in pkMap else '',
                    'autoincrement' : 'yes' if bAutoIncrement else '',
                }   
                
                curTable['columns'].append(curCol)

            self.dumpTable(curTable, of)
            
    def dumpTable(self, info, of):
        colDefs = []
        keys = []
        for col in info['columns']:
          colDefs.append(self.ddlInterface.quoteName(col['name']) + " " + self.ddlInterface.retColTypeEtc(col))
          if 'key' in col and col['key'] == 1:
            keys.append(col['name'])

        results = []
        self.ddlInterface.addTable(info['name'],colDefs,keys,[],results)

        for index in info['indexes']:
          if not index[3]:
            self.ddlInterface.addIndex(info['name'],index[0],index[1],results)

        for index in info['relations']:
          self.ddlInterface.addRelation(info['name'],index[0],index[1][0],index[2],index[3][0],index[4],index[5],results)
          
        for result in results:
          print "%s;" % (result[1])

def createDownloader(conn = None, info = None, options = None):
    db = OracleDownloader()

    if conn:
        db.useConnection(conn, info['version'])
    elif info:
        db.connect(info)
    else:
        info = conn_info[dbms]
        db.connect(info)
        
    return DownloadXml(db, options)

def parseCommandLine():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("", "--host",
        dest="strHost", metavar="HOST", default="localhost",
        help="Hostname or IP of machine")
    parser.add_option("-d", "--dbname",
        dest="strDbName", metavar="DATABASE", 
        help="Dowload for which named Database")
    parser.add_option("-u", "--user",
        dest="strUserName", metavar="USER", 
        help="User to login with")
    parser.add_option("-p", "--pass",
        dest="strPassword", metavar="PASS", 
        help="Password for the user")

    parser.add_option("-t", "--tables",
        dest="strTables", metavar="TABLES", default=None,
        help="Comma separated list of tables")

    (options, args) = parser.parse_args()
    
    info = {
        'dbname' : options.strDbName, 
        'user'   : options.strUserName, 
        'pass'   : options.strPassword,
        'host'   : options.strHost,
        'version' : 99,
    }

    if options.strTables:
        tables = options.strTables.split(',')
    else:
        tables = None
        
    runOptions = {
        'getrelations' : True,
        'getindexes'   : True,
        'tables'       : tables,
    }
    if info['dbname'] == None or info['user'] == None:
        parser.print_help()
        sys.exit(-1)
        
    cd = createDownloader(info = info, options = runOptions)
    cd.downloadSchema()

if __name__ == "__main__":
    parseCommandLine()
