
// init websocket
let ws;
let id;
let msgq = [];
let waitinglist = {};
let qrunning = false;
const wsport = 18000
let LS = localStorage;
let email = "";
let pass = "";
setstore("signed in", false);


$('document').ready(function(){wsinit();});

function wsinit(){
ws = new WebSocket("ws://" + location.host.split(":")[0] + ":" + wsport);
ws.onopen = function(e) {
  if (qrunning == false){
    qrunning = true;
    msghandler()
  }
  console.info("[open] Connection established");
  
};

ws.onmessage = function(event) {
  console.info(`[message] Data received from server: ${event.data}`);
  msgq.push(event.data)
  msghandler()
};

ws.onclose = function(event) {
  if (event.wasClean) {
    console.warn(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
  } else {
    // e.g. server process killed or network down
    // event.code is usually 1006 in this case
    console.warn('[close] Connection died');
  }
  setstore("signed in", false);
  ws.close()
  setTimeout(wsinit, 5000);
};

ws.onerror = function(error) {
  console.error(`[error] ${error.message}`);
  setstore("signed in", false);
  ws.close();
  setTimeout(wsinit, 5000);

};
};


async function sendmsg({category="admin", type="msg", data={}, metadata={}, getresult=false}={}){
    // note: getresult will return the "data" part of the response
    if (getresult){
        guid = getguid()
        waitinglist[guid] = null;
        metadata = {"copy":{"guid":guid}} // so the server understands to copy it
    }
    
    data["id"] = getstore("id");
    data["sessiontoken"] = getstore("session_token")
    var msg = JSON.stringify({"category": category, "type":type, "data":data, "metadata":metadata});
    console.info("Sending message: " + msg);
    ws.send(msg);

    if (getresult){
        return guid
    }
}

async function getresult(guid){
    console.trace(`Waiting for guid; ${guid}`)
    await until(_ => (waitinglist[guid] != null));
    result = waitinglist[guid];
    console.info(`returning ${JSON.stringify(result)} for guid: ${guid}`)
    delete waitinglist[guid];

    return result
}

function setstore(key, value){
    return LS.setItem(key, JSON.stringify(value))
}

function getstore(key){
    return JSON.parse(LS.getItem(key))
}


function msghandler(){
    
    for (x in msgq){
        console.info("in msghandler")
        var msg = JSON.parse(msgq[x]);
        let {category, type, data, metadata} = msg;
        data = data["resource"]
        console.log(data)
        let cat = category
        
        if (cat == "admin"){
            if (type == "signupresponse"){
                id=data["id"]
                console.log(id)
                paircode = data["pcode"]
                setstore("id",id)
                setstore("pcode", paircode);
                console.info("Signed up.")
                showDigits(paircode)
            } else if(type == "signinresponse"){
                console.log("signed in succesfully")
                console.log(data)
                token = data["token"]
                rloc = data["redirect"]
                console.log("redirecting to " + rloc)
                window.location.replace(rloc);
            } else if(type == "mfaresponse"){
              res = data["feedback"]
              showDigits(res)
              document.getElementById('registerNumber').style.color="green";
            }
        } else if (data["status"] == 407){
            alert("please register again, we've lost your phone")
        }


        msgq.shift();
    }
    //setInterval(msghandler, 200);
}


function getguid(){
    return Math.random().toString(36).replace(/[^a-z]+/g, '').substr(2, 4);
}


// helper
function until(conditionFunction) { // from: https://stackoverflow.com/a/52657929
    // usage:  await until(_ => (condition));
  const poll = resolve => {
    if(conditionFunction()) resolve();
    else setTimeout(_ => poll(resolve), 100);
  }

  return new Promise(poll);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function randrange(min, max) { // min and max included 
  return Math.floor(Math.random() * (max - min + 1) + min)
}

function getbyid(id){
  return document.getElementById(id);
}
