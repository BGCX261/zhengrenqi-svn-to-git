'''
Created on 2010-4-23

@author: zhengrenqi
'''
import time
import logging
class Clock:
  """ Helper class for code profiling """
  RUNNING = 1
  STOP = 2
  def __init__(self):
    self.timers = {'total':{ "time":time.clock(), "status":self.RUNNING}}
  def start(self, timerName):
    #print "start be self.timers[timerName]",self.timers.get(timerName, 0)
    #print "start time.clock()",time.clock()
    if not self.timers.has_key(timerName):
      self.timers[timerName] = {"time": 0, "status":self.STOP}

    if self.timers[timerName]["status"] != self.STOP:
      return
    self.timers[timerName]["time"] = time.clock() - self.timers[timerName]["time"]
    self.timers[timerName]["status"] = self.RUNNING

    #print "start af self.timers[timerName]",self.timers[timerName]
  def stop(self, timerName):
    
    if not self.timers[timerName] and self.timers[timerName]["status"] != self.RUNNING:
      return
    #print "stop self.timers[timerName]",self.timers[timerName]
    self.timers[timerName]["time"] = time.clock() - self.timers[timerName]["time"]
    self.timers[timerName]["status"] = self.STOP

  def clear(self, timerName):
    if self.timers.has_key(timerName):
      self.timers[timerName]["status"] = self.STOP
      self.timers[timerName]["time"] = 0
  def value(self, timerName):
    if not self.timers[timerName]:
      return
    self.stop(timerName)
    return "%.3f" % (self.timers[timerName]["time"])

zclock = Clock()

if __name__ == '__main__':
    pass
