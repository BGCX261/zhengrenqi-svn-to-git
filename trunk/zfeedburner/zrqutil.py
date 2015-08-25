# -*- coding: utf-8 -*-
'''
Created on 2010-7-9

@author: ֣郑仁启
'''
import feedparser
import re
import fetchpage

fetch_page = fetchpage.fetch_page
fetch_content = fetchpage.fetch_content
def _parse_date_wsj(dateString):
  wsj_date_format_re = re.compile(u'(\d{4})/(\d{,2})/(\d{,2})[\s{0,2}|T](\d{,2}):(\d{,2}):(\d{,2})\s{,2}(\+|-)(\d{,2})(\d{2})')
  m = wsj_date_format_re.match(dateString)
  if not m: return
  w3dtfdate = '%(year)s-%(month)s-%(day)sT%(hour)s:%(minute)s:%(second)s%(zone0)s%(zone1)s:%(zone2)s' % \
              {'year': m.group(1), 'month': m.group(2), 'day': m.group(3), \
               'hour': m.group(4), 'minute': m.group(5), 'second': m.group(6), \
               'zone0': m.group(7), 'zone1': m.group(8), 'zone2': m.group(9)}
  return feedparser._parse_date_w3dtf(w3dtfdate)
  pass
feedparser.registerDateHandler(_parse_date_wsj)
