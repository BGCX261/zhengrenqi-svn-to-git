# -*- coding: utf-8 -*-
'''
Created on 2010-7-9

@author: ֣郑仁启
'''
from cgi import parse_header
from google.appengine.api import urlfetch
import feedparser
import re
import string


def fetch_page(url, cut_content_from, cut_content_to):
  resp = urlfetch.fetch(url)
  html_content = resp.content
  
  charset = get_charset(html_content)
  content_tag_start = html_content.find(cut_content_from)
  content_tag_end = html_content.find(cut_content_to, content_tag_start)
  content = html_content[content_tag_start + len('<!content_tag txt>'):content_tag_end].decode(charset)

  return content
  pass

def get_charset(html_content):
  i = 0
  while True:
    i = html_content.find('<meta', i)
    if i == -1:
      break
    attrfind = re.compile(
        r'\s*([a-zA-Z_][-.:a-zA-Z_0-9]*)(\s*=\s*'
        r'(\'[^\']*\'|"[^"]*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~@]*))?')
    tagfind = re.compile('[a-zA-Z][-.a-zA-Z0-9:_]*')
    match = tagfind.match(html_content, i + 1)
    endpos = check_for_whole_start_tag(html_content, i)
    k = match.end()
    attrs = []
    while k < endpos:
      m = attrfind.match(html_content, k)
      if not m:
          break
      attrname, rest, attrvalue = m.group(1, 2, 3)
      if not rest:
          attrvalue = None
      elif attrvalue[:1] == '\'' == attrvalue[-1:] or \
           attrvalue[:1] == '"' == attrvalue[-1:]:
          attrvalue = attrvalue[1:-1]
      attrs.append((attrname.lower(), attrvalue))
      k = m.end()
    for attr in attrs:
      if attr[0] == 'http-equiv' and string.lower(attr[1]) == 'content-type':
        for attr in attrs:
          if attr[0] == 'content':
            (ct, parms) = parse_header(attr[1])
            if parms.has_key('charset'):
              return parms['charset']
        break
    i = endpos
  return 'UTF-8'
def check_for_whole_start_tag(rawdata, i):
    locatestarttagend = re.compile(r"""
      <[a-zA-Z][-.a-zA-Z0-9:_]*          # tag name
      (?:\s+                             # whitespace before attribute name
        (?:[a-zA-Z_][-.:a-zA-Z0-9_]*     # attribute name
          (?:\s*=\s*                     # value indicator
            (?:'[^']*'                   # LITA-enclosed value
              |\"[^\"]*\"                # LIT-enclosed value
              |[^'\">\s]+                # bare value
             )
           )?
         )
       )*
      \s*                                # trailing whitespace
    """, re.VERBOSE)
    m = locatestarttagend.match(rawdata, i)
    if m:
        j = m.end()
        next = rawdata[j:j + 1]
        if next == ">":
            return j + 1
        if next == "/":
            if rawdata.startswith("/>", j):
                return j + 2
            if rawdata.startswith("/", j):
                # buffer boundary
                return - 1
            # else bogus input
        if next == "":
            # end of input
            return - 1
        if next in ("abcdefghijklmnopqrstuvwxyz=/"
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            # end of input in or before attribute value, or we have the
            # '/' from a '/>' ending
            return - 1
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
