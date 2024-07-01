#!/usr/bin/python3

#!#--- for use with wsgi, otherwise ignore --- #!#
import sys, os, secrets
import logging
logging.basicConfig(stream=sys.stderr)

print(os.path.join(os.getcwd(), "data/site/"))
sys.path.insert(0,os.path.join(os.getcwd(), "data/site/"))
print("----------")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)) + "/")


from components.site import Site
application = Site().app
application.secret_key = secrets.token_hex()

print(application)
