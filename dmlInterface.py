#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re, os
from OracleInterface import DmlOracle
from PostgreSQLInterface import DmlPostgres
from MySqlInterface import DmlMySql
from FirebirdInterface import DmlFirebird

#print "in ddlinterface.py"
#exit()

__author__ = "Scott Kirkwood (scott_kirkwood at berlios.com)"
__keywords__ = ['XML', 'DML', 'SQL', 'Databases', 'Agile DB', 'ALTER', 'CREATE TABLE', 'GPL']
__licence__ = "GNU Public License (GPL)"
__url__ = 'http://xml2dml.berlios.de'
__version__ = "$Revision: 0.2 $"


def attribsToDict(node):
    dict = {}
    attribs = node.attributes
    for nIndex in range(attribs.length):
        dict[attribs.item(nIndex).name] = attribs.item(nIndex).value
    
    return dict

def createDmlInterface(strDbms):
    """ Here we use the letter/envelope paradymn to create the class of the right
    type. """ 
    
    if strDbms.startswith('postgres'):
        return DmlPostgres(strDbms)
    elif strDbms.startswith('mysql'):
        return DmlMySql(strDbms)
    elif strDbms.startswith('firebird'):
        return DmlFirebird(strDbms)
    elif strDbms.startswith('oracle'):
        return DmlOracle(strDbms)
    else:
        assert(False)
        
if __name__ == "__main__":
    import os, sys
    sys.path += ['../tests']
    from diffXml2DdlTest import doTests
    
    os.chdir('../tests')
    doTests()
