# -*- coding: utf-8 -*-
'''
Created on 2010-4-21

@author: zhengrenqi
'''
import datetime
#import pytz
import string
import time
import unittest
import ztools


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testClock(self):
      a = ztools.Clock()
      a.start('countClock2')
      dt = datetime.datetime.utcnow()
      for i in range(1):
        s = ""
        for j in range(100000):
          s = s + str(j)
      print datetime.datetime.utcnow() - dt
      a.stop('countClock2')
      print a.value('countClock2')

    def testMicrosecond (self):
      dt = datetime.datetime.utcnow()
      print dt.tzinfo
      print dt
      print dir(dt)
      
    def testSplit(self):
      s = "CN	+3114+12128	Asia/Shanghai	east China - Beijing, Guangdong, Shanghai, etc."
      print s
      print s.split(None, 4)[:3]
#      print pytz.country_timezones('cn')
#      tz = pytz.timezone('Asia/Shanghai')
#      dt = datetime.datetime(2009, 2, 21, 15, 12, 33, tzinfo=tz)
#      print repr(dt)
#      tz = pytz.timezone('US/Pacific')
#      dt = datetime.datetime(2009, 2, 21, 15, 12, 33, tzinfo=tz)
#      print repr(dt)
      dt = datetime.datetime.fromtimestamp(string.atof('1272089379.187'))
      print repr(dt)
      print dt.microsecond
      print time.time()
      print string.atof(time.time())
      s3 = """
      1234
      4312  
      adsdad
      """
      print s3.split()
      
      
    def testStr(self):
      print "the type is %s" % type(time.time())
      print ''.join(["bookmark_" , str(time.time())])
      p = []
      p.append('a')
      p.append(12)
      print p
      print '_'.join([str(s) for s in p])

      b = []
      count = 0
      b.append("h1")
      size = len(b)
      print b[count:size - 1]
      count = size

      b.append("a")
      b.append("a")
      b.append("a")
      b.append("a")
      b.append("h3")
      size = len(b)
      print b[count:size - 1]
      count = size

      b.append("a")
      b.append("a")
      b.append("a")
      b.append("a")
      b.append("h3")
      size = len(b)
      print b[count:size - 1]
      count = size
      pass
    def testList01(self):
      ls = ['a']
      print ls
      ls2 = ['b', 'c']
      ls.extend(ls2)
      print ls
    def testList02(self):
      print '--------testList02'
      ls = ['a']
      print ls
      ls.append('b')
      ls.append('c')
      print 'c' in ls
      print ls[-1]

if __name__ == "__main__":
    import sys;sys.argv = ['', 'Test.testList02']
    unittest.main()
