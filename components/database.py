from ast import literal_eval as eval
from components.logger import Logger
import json, traceback, inspect, random, os, sqlite3
from sqlitedict import SqliteDict
from components.logger import Logger

class Database:
    def __init__(self):
        self.logger = Logger("Database").logger
        datadir = os.path.join(os.getcwd(), "data")
        self.db = os.path.join(datadir, "main.db")
        self.table = "main"
        self.userresponse = {}
        with SqliteDict(":memory:", autocommit=True, encode=json.dumps, decode=json.loads) as dbdict:
            self.membase = {}
    
    
    def gettable(self, table):
        res = ""
        try:
            with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
                res = dbdict[table]
            msg = {"status": "200", "resource":res, "success": True}
            return msg
        except:
            msg = {"status": 404, "resource": f"table: \"{table}\" not found", "success": False}
            return msg

    def gettables(self):
        try:
            with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
                res = dict(dbdict)
            msg = {"status": "200", "resource":res, "success": True}
            return msg
        except Exception as e:
            self.logger(traceback.format_exc())
            self.logger(e, "alert", "red")
            msg = {"status": 404, "resource": f"Couldn't list tables.", "success": False}
            return msg

    def write(self, key, value, table, update =True):
        """Usage: Database().write("foo", {"foo":"bar"}, "test")"""

        key = json.loads(json.dumps(key))
        if type(key) != str:
            key = str(key)

        value = json.loads(json.dumps(value))
        if type(value) == str: # can only replace
            update = False
        with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
            if table not in dbdict.keys():
                dbdict[table] = {}
                self.logger(f"created table: {table}", "debug")
                dbdict.commit()

            tdict = dbdict[table]

            if key not in tdict: # can't update something that doesn't exist, so check first
                update = False
            if update:
                if type(tdict[key]) == list:
                    if type(value) == list: # loop through
                        for item in value:
                            tdict[key].append(item)
                    else:
                        tdict[key].append(value)
                elif type(tdict[key]) == dict:
                    if type(value) != dict:
                        self.logger(f"{value} is the wrong type. should be dict", "warning", "yellow")
                        return
                    for k,v in value.items():
                        tdict[key][k] = v
            else:
                tdict[key] = value # add actual data
            dbdict[table] = tdict # save back into dbdict
            dbdict.commit() # then commit

    def query(self, query, table= "main"):
        """Usage: 
            Database().query("city", "users") or:
        """

        if len(query) == 1:
            query = query[0]
        try:
            res = ""
            with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
                data = dbdict[table]
                if type(query) == str:
                    res = data[query]
                if type(query) == list: #e.g. ..query(["lastshow", "title"])
                    for q in query:
                        data = data[q]
                    res = data
            msg = {"status": "200", "resource":res, "success": True}
            return msg
        except KeyError as e:
            res = {"status": "404", "resource": f"Query: \"{query}\" not found", "success": False}
            return res

    def remove(self, query, table, cleartable = False):
        try:
            res = ""
            with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
                data = dbdict[table]

                if cleartable:
                    del dbdict[table]
                else:
                    del data[query]
                    dbdict[table] = data

                dbdict.commit()
            msg = {"status": "200", "success": True}
            return msg

        except KeyError as e:
            res = {"status": "404", "resource": f"Query: \"{query}\" not found", "success": False}
            self.logger(res, "info", "yellow")
            answer = self.getfromuser({"q":query, "t": table})
            if answer:
                return self.query(query, table)
            else:
                return res

    def cleartable(self, table):
        try:
            res = ""
            with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
                data = dbdict[table]
                dbdict[table] = {}
                dbdict.commit()
            msg = {"status": "200", "success": True}
            return msg

        except KeyError as e:
            res = {"status": "404", "resource": f"Query: \"{table}\" not found", "success": False}
            self.logger(res, "info", "yellow")
            return res