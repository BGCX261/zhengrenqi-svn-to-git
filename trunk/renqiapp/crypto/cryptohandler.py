# -*- coding: utf-8 -*-
'''
Created on 2010-4-21

@author: zhengrenqi
'''
from base import requires_admin, BaseRequestHandler
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import logging

DB_TIME = 0

class CryptoAES256Handler(BaseRequestHandler):

  @requires_admin
  def get(self):
    logging.debug('BookmarkHandler')
    
    self.render("template/crypto/AES.html", {})
    pass

  def post(self):

    self.redirect('/bookmark')


def main():
  application = webapp.WSGIApplication([('/crypto/aes', CryptoAES256Handler)
                                        ], debug = True)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
