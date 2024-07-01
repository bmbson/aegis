import websockets, asyncio, json, os, tracemalloc, shortuuid, ssl, traceback, socket
from components.logger import Logger
from components.security import Security


class Networking:

    def __init__(self, db):
        self.logger = Logger("Networking").logger
        self.db = db
        self.security = Security(db)
        self.wsport = 18000
        self.httpport = 18443

    async def runserver(self, websocket, path):
        self.logger("got new client!", "info", "yellow")
        while True:
            try:
                data = await websocket.recv()
                msg = json.loads(data)
                await self.msghandler(websocket, msg)
                await asyncio.sleep(0.1)
            except ConnectionResetError as e1:
                self.logger("Reset error", "alert", "red")
                await asyncio.sleep(2)
                raise ConnectionResetError
                break
            except Exception as e2:
                # use re for error parsing
                traceback.print_exc()
                self.logger(f"error: {e2}", "alert", "red")
                if "1001" in str(e2) or "1005" in str(e2):
                    self.logger(f"Error: {str(e2)}", "alert", "red")
                    await websocket.close()
                    self.logger("1-closed.")
                    break
                else:
                    """ other error """
                    self.logger(str(e2))

                    res = self.messagebuilder("admin", "error", {"code":400, "error":"Malformed request"})
                    await websocket.send(res)
                    await websocket.close()
                    self.logger("2-closed.")
                    break
            await asyncio.sleep(0)


    def createguid(self, size=4):
        return shortuuid.uuid()[:size]   

    async def msghandler(self, websocket, msg):
        self.logger(f"got message! - {msg}")
        category = msg["category"]
        qtype = msg["type"]
        data = msg.get("data",{})
        metadata = msg.get("metadata",{})
        res = None

        if category == "admin":
            if qtype == "authresponse":
                authcode = data.get("authcode", None)
                pcode = data.get("pcode", None)
                id = self.db.membase[pcode]
                hashcode = self.security.get_mfa_token(id)["resource"]["mfacode"]
                check = self.security.assertpasswd(authcode, hashcode)
                if check:
                    self.logger("Succesfully authenticaed using mfa. Redirecting.")
                    msg = self.messagebuilder("admin", "signinresponse", {"resource":{"redirect": f"http://{self.ownIP()}:{self.httpport}/success.html", "token": "[jwt token]"}}) #  placeholders
                    ws = self.db.membase[id]["loginsocket"]
                    await ws.send(msg)

            if qtype == "pairing":
                pcode = data.get("pcode", None)
                if pcode in self.db.membase:
                    # save websocket
                    id = self.db.membase[pcode]
                    self.db.membase[id]["mfasocket"] = websocket
                    
                    # send clearmfa to phone, which will save it and send it back to verify later
                    mfacode = self.security.generate_mfa_token(id)["resource"]["clearmfacode"]
                    res = self.messagebuilder("admin", "pairingresponse", {"mfacode": mfacode, "pcode": pcode})
                    mfacode = None

                    msg = self.messagebuilder("admin", "mfaresponse", {"resource":{"feedback": "succesfully paired."}})
                    
                    ws = self.db.membase[id]["loginsocket"]
                    await ws.send(msg)
                    self.logger(f"Succesfully paired phone to user with id {id}")
                    # now the phone is paired to the id!

            if qtype == "signin":
                self.logger("Got sign-in request!")
                email = data.get("email", None)
                if email == None:
                    res = self.messagebuilder("admin", "signin", {"success": False, "status":401})
                else:   
                    id = self.security.getuserid(email)["resource"]["id"]
                    self.logger(f"user has id: {id}")
                    if self.security.userexists(id):                   
                        passcheck = self.security.checkcreds({"email":email, "password": data["password"]})
                        if passcheck["success"]: # creds are good, move on to 2fa
                            self.logger("Moving to 2fa")
                            if "mfasocket" in self.db.membase.get(id, {}):
                                ws = self.db.membase[id]["mfasocket"]
                                msg = self.messagebuilder("admin", "authrequest", {"sitename": "internal.amd.com"}) # sitename here is placeholder
                                await ws.send(msg)
                                res = self.messagebuilder("admin","empty", {},{})                              
                            else:
                                res = self.messagebuilder("admin", "signin", {"success": False, "status":407}) # additional authentication required
                        else:
                            res = self.messagebuilder("admin", "signin", {"success": False, "status":401}) # unauthorized
                    else:
                        res = self.messagebuilder("admin", "signin", {"success": False, "status":401}) # unauthorized
            if qtype == "signup":
                self.logger("got sign up request")
                if "email" in data.keys():
                    email = data["email"]

                    # create new user
                    result = self.security.adduser(data["email"], data["password"])
                    id = result["resource"]["id"]
                    pcode = result["resource"]["pcode"]
                    self.db.membase[id] = {"loginsocket":websocket}
                    res = self.messagebuilder("admin", "signupresponse", {"success": True, "status":200, "resource": result["resource"]})

                    self.logger(f"signed up new user with email: {email}. Their pairing code is {pcode}, which is linked to id: {id}")
                    self.db.membase[pcode] = id
        if res:
            await websocket.send(res)

    def messagebuilder(self, category, msgtype, data={}, metadata={}):
        msg = json.dumps({"category":category, "type":msgtype, "data":data, "metadata":metadata})
        return msg


    async def run_straglers(self):
        while True: 
            await asyncio.sleep(0)

    def ownIP(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        res = s.getsockname()[0]
        s.close()
        return res

    def startserving(self):
        tracemalloc.start()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.db.membase["eventloop"] = self.loop

        # check if tls/ssl is available
        ssl_enabled = False
        protocol = "ws"
        if ssl_enabled:
            certchain_location = "cert.pem"
            keyfile_location = "privatekey.pem"
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certchain_location, keyfile= keyfile_location)
            self.logger("Using SSL")
            protocol = "wss"
        else:
            ssl_context = None
            self.logger("Not using ssl. Connection is insecure")
        
        self.logger(f"Serving websockets on {protocol}://{self.ownIP()}:{self.wsport}")
        serveserver = websockets.serve(self.runserver, "0.0.0.0", self.wsport, ssl=ssl_context)
        
        self.loop.create_task(self.run_straglers())
        asyncio.ensure_future(serveserver)
        self.loop.run_forever()
        self.logger("Waiting for connections..")

if __name__ == "__main__":
    Networking().startserving()
