from components.logger import Logger
import shortuuid, bcrypt

class Security:
    """
        do user authentication
    """
    def __init__(self, Database):
        self.db = Database
        self.logger = Logger("Security").logger
        self.sessiontime = 3600
        self.db.membase["sessions"] = {}

    def checkcreds(self, data):
        """data contains {"email": "test@test.com", "password": "strongpassword"}"""
        email = data["email"]
        password = data["password"]
        res = self.getuserid(email)
        if res["success"]:
            id = res["resource"]["id"]
            self.logger(f"checking creds for user {email} - {id}")
            authres = self.checkuserpasswd(id, password)
            if authres["success"]:
                return {"success":True, "resource":authres["resource"]}
            else:
                return {"success": False, "resource": 403}
        else:
            return {"success": False, "resource": 401}
        
    def getuser(self, userid): 
        cleandata = self.db.query(userid, "users")["resource"]          
        del cleandata["password"] # not sharing the password
        return {"success":True, "resource":cleandata}

    def createid(self, size=8):
        return shortuuid.uuid()[:size]

    def adduser(self, email, password):
        
        plainpwd = password
        id = self.createid()
        userdata = {}
        userdata["id"] = id
        userdata["session"] = {}
        userdata["email"] = email
        self.logger(f"adding user {email} - {id}")
        userdata["password"] = self.hashpasswd(plainpwd)

        
        pcode = self.createid(4).lower() # pairing code
        userdata["pcode"] = pcode
        self.db.cleartable("users") # introduces problems with searching for id later
        self.db.write(id, userdata, "users", update=False)
        return {"success": True, "resource":{"id": id, "pcode": pcode}}

    def generate_mfa_token(self, id):
        """ hashes a random string and saves it to user."""
        mfacode = self.createid(16)
        self.db.write(id, {"mfacode":self.hashpasswd(mfacode)}, "users", update=True)
        return {"success": True, "resource":{"clearmfacode": mfacode}}

    def get_mfa_token(self, id):
        mfacode = self.db.query(id, "users")["resource"]["mfacode"]
        return {"success": True, "resource":{"mfacode": mfacode}}

    def userexists(self, id):
        if id in self.db.gettable("users")["resource"].keys():
            return {"success":True, "resource":{"id":id}}
        else:
            return {"success":False, "resource":None}
        return id in self.db.gettable("users")["resource"].keys()

    def issessiontokenvalid(self,id):
        tokenobj = self.db.membase["sessions"].get(id, {})
        if "expires_at" in tokenobj["session"].keys() and tokenobj["session"]["expires_at"] > int(time.time()):
            self.logger("sessiontoken is valid")
            return {"success": True, "resource":{"status":"valid"}}
        self.logger("sessiontoken is invalid")
        return {"success": False, "resource":{"status":"invalid"}}

    def getuserid(self, query):
        userlist = self.db.gettable("users")["resource"]
        for uid in userlist:
            uemail = userlist[uid]["email"]
            if query in userlist[uid].values():
                return {"success":True, "resource":{"id":uid}}
        return {"success":False, "resource":None}

    def checkuserpasswd(self, userid, plaintext):
        try:
            hashpwd = self.db.query(userid, "users")["resource"]["password"]
            res = self.assertpasswd(plaintext, hashpwd)
            if res:
                return {"success":True, "resource":res}
            else:
                return {"success":False, "resource": 403}

        except Exception as e:
            print(e)
            return {"success":False, "resource": 400}

    def hashpasswd(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def assertpasswd(self, password, hashed_password):
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def gettoken(self, id):
        if not self.userexists(id):
            return None
        token = self.db.membase["sessions"][id]["session"].get("token", None)
        return token


    def isauthed(self, id, sessiontoken = None):
        if id == None or sessiontoken == None:
            return False
        if self.gettoken(id):
            return self.issessiontokenvalid(id)["success"]
        else:
            return False
