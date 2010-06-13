#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
import re, os

class DmlCommonInterface:
    """ Class which has the common interfaces for creating DDL.  
    
      You normally don't use this class alone but derive a subclass which will handle how
      your class differs from the standard. (Not that DdlCommonInterface really follows a standard)
    """
    def __init__(self, strDbms):
        self.dbmsType = strDbms
