document.addEventListener("DOMContentLoaded", function(event) {

// read form

function submitlogin(){
    let email = document.getElementById("usernameField").value
    let password = document.getElementById("passwordField").value
    ws.send(JSON.stringify({"category":"admin","type":"signin","data":{"email":email, "password":password},"metadata":{}}))
    alert("please look at your phone and authenticate")
  }

function submitregister(){
let email = document.getElementById("usernameField").value
let password = document.getElementById("passwordField").value
ws.send(JSON.stringify({"category":"admin","type":"signup","data":{"email":email, "password":password},"metadata":{}}))
}

let loginbtn = document.getElementById("login-btn")
let registerbtn = document.getElementById("register-btn")
loginbtn.addEventListener("click", submitlogin)
registerbtn.addEventListener("click", submitregister)


function showpcode(id, code){
    // cleanup
    loginform.removeEventListener("submit", handleSubmit)
    loginform.remove()
}


});
