#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re, os, sys
from xml.sax.saxutils import escape 
from downloadCommon import getSeqName
from xml.dom.minidom import parse, parseString
from OracleInterface import OracleDownloader
from ddlInterface import createDdlInterface, attribsToDict
from dmlInterface import createDmlInterface
from DdlCommonInterface import g_dbTypes


__author__ = "Scott Kirkwood (scott_kirkwood at berlios.com)"
__keywords__ = ['XML', 'DML', 'SQL', 'Databases', 'Agile DB', 'ALTER', 'CREATE TABLE', 'GPL']
__licence__ = "GNU Public License (GPL)"
__url__ = 'http://xml2dml.berlios.de'


class DownloadSchema:
    def __init__(self, downloader, options):
        self.db = downloader
        self.options = options
        self.ddlInterface = createDdlInterface(self.options['toschema'])
        self.dmlInterface = createDmlInterface(self.options['toschema'])
        
    def downloadSchema(self, of = sys.stdout):
        if self.options['getall'] == True or (self.options['tables'] and (len(self.options['tables']) > 0)):
            self.getTables(of)

        if self.options['getall'] == True or (self.options['tables'] and (len(self.options['tables']) > 0)):
            self.getTableData(of)

        if self.options['getall'] == True or (self.options['views'] and (len(self.options['views']) > 0)):
            self.getViews(of)


    def getTableData(self, of):
        tables = self.db.getTables(tableList = self.options['tables'])
        for strTableName in tables:
            cols = self.db.getTableColumns(strTableName)
            table_data_iter = self.db.getTableData(strTableName,cols)
            self.dumpTableDML(strTableName, cols, table_data_iter)

            
    def getTables(self, of):
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

                curCol = dict( 
                  [
                    ('name', str(strColumnName)),
                    ('type', self.db.type_to_standard(str(type))),
                    ('size', attlen) if attlen else ('',''),
                    ('precision', precision) if precision else ('',''),
                    ('default', default) if default else ('',''),
                    ('desc', escape(strComment)) if strComment else ('',''),
                    ('null', 'no') if attnotnull else ('',''),
                    ('key', pkMap[strColumnName]) if strColumnName in pkMap else ('',''),
                    ('autoincrement', 'yes') if bAutoIncrement else ('','')
                  ] );
                  
                curTable['columns'].append(curCol)

            self.dumpTableDDL(curTable, of)

    def getViews(self, of):
        views = self.db.getViews(self.options['views'])
        for viewName in views:
            definition = self.db.getViewDefinition(viewName)
            info = {
                'name' : viewName,
                'definition' : definition,
            }
            self.dumpView(info, of)
    
    def dumpView(self, info, of):
        results = []
        self.ddlInterface.addView(info['name'],info['definition'],{},results)

        for result in results:
          print "%s;" % (result[1])

    def dumpTableDDL(self, info, of):
        colDefs = []
        keys = []
        for col in info['columns']:
          colDefs.append(self.ddlInterface.quoteName(col['name']) + " " + self.ddlInterface.retColTypeEtc(col))
          if 'key' in col and col['key'] == 1:
            keys.append(col['name'])

        results = []
        self.ddlInterface.addTable(info['name'],colDefs,keys,'',results)

        for index in info['indexes']:
          if not index[3]:
            self.ddlInterface.addIndex(info['name'],index[0],index[1],results)

        for index in info['relations']:
          self.ddlInterface.addRelation(info['name'],index[0],index[1][0],index[2],index[3][0],index[4],index[5],results)
          
        for result in results:
          print "%s;" % (result[1])

    def dumpTableDML(self, strTableName, cols, table_data_iter):
        for line in self.dmlInterface.insertData(strTableName, cols, table_data_iter):
            print line

def createDownloader(conn = None, info = None, options = None):
    db = OracleDownloader()

    if conn:
        db.useConnection(conn, info['version'])
    elif info:
        db.connect(info)
    else:
        info = conn_info[dbms]
        db.connect(info)
        
    return DownloadSchema(db, options)

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

    parser.add_option("-a", "--getall",
        action="store_true", dest="bGetAll", default=False,
        help="Download all tables and views for database")

    parser.add_option("-t", "--tables",
        dest="strTables", metavar="TABLES", default=None,
        help="Comma separated list of tables")

    parser.add_option("-v", "--views",
        dest="strViews", metavar="VIEWS", default=None,
        help="Comma separated list of views")

    parser.add_option("", "--toschema",
        dest="toSchema", metavar="TOSCHEMA", default="oracle",
        help="Output schema for SQL - mysql/oracle/postgresql")
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
        
    if options.strViews:
        views = options.strViews.split(',')
    else:
        views = None

    runOptions = {
        'toschema'     : options.toSchema,
        'getall'       : options.bGetAll,
        'gettables'    : True if ((tables and len(tables) > 0)) else False,
        'getviews'     : True if ((views and len(views) > 0)) else False,
        'getrelations' : True,
        'getindexes'   : True,
        'tables'       : tables,
        'views'        : views,
    }
    if info['dbname'] == None or info['user'] == None or options.toSchema not in g_dbTypes:
        parser.print_help()
        sys.exit(-1)
        
    cd = createDownloader(info = info, options = runOptions)
    cd.downloadSchema()

if __name__ == "__main__":
    parseCommandLine()
