# -*- coding: utf-8 -*-
'''
Created on 2010-6-3

@author: 郑仁启
'''
import unittest
from wsjnews.newshandler import NewsParser


class Test(unittest.TestCase):


  def setUp(self):
    pass


  def tearDown(self):
    pass


  def testNewsParser(self):
    parser = NewsParser()
    parser.feed(html)
    pass
html = open('test.htm').read()

if __name__ == "__main__":
  #import sys;sys.argv = ['', 'Test.testNewsParser']
  unittest.main()