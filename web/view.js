function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

function announce(socket, name){
    var msg = {name:name, verb: 'announce'};
    socket.send(JSON.stringify(msg));
    document.getElementById("fname").value = name;
}

function connect(){

    const socket = new WebSocket('ws://casten.net:8081');

    // Connection opened
    socket.addEventListener('open', function (event) {
        document.getElementById("disconnected").hidden = true;
        document.getElementById("connected").hidden = false;
        var name = getUrlVars()['fname']
        if (name != undefined) {
	     announce(socket,name);
        }
    });

    socket.addEventListener('close', function(event){
        document.getElementById("disconnected").hidden = false;
        document.getElementById("connected").hidden = true;
	var name = document.getElementById("fname").value;
        var retry = setInterval(function(){
            reconnect(socket, name, retry);
        },1000)
    });

    // Listen for messages
    socket.addEventListener('message', function (event) {
        processServerMessage(event.data);
    });

    var lastPress = 0; 
    var lastSent = '';
    var nameField = document.getElementById("fname")
    nameField.addEventListener("keyup", function(event) {
        lastPress = Date.now();
        setTimeout(function(){
	    var now = Date.now();
	    var currValue = document.getElementById("fname").value;
	    if (((now - lastPress) > 3000) && (lastSent != currValue)) {
	        announce(socket,currValue)
                lastSent = currValue;
	    }
        },3000);
        event.preventDefault();
    });

    var send = document.getElementById("send");
    send.addEventListener("click", function(){
                                      handleSend(socket);
                                   }
                         );

    return true;
}

function reconnect(socket, name, retry) {
    if (connect()){
	announce(socket, name);
        clearInterval(retry);
    }
}

function processServerMessage(msg) {
    try {
        var data = JSON.parse(msg);
        var destCtrl;
        switch (data.verb) {
            case "broadcast":
                destCtrl = document.getElementById("broadcast_text");
                destCtrl.value += data.msg+'\n';
                break;
            case "private":
                destCtrl = document.getElementById("personal_text");
                destCtrl.value += data.msg+'\n'
                break;
            case "updateConnected":
                var select = document.getElementById('recipient');
                var selected = document.getElementById("recipient").value;
                var options = select.options;
                for (i = options.length-1; i >= 0; i--) {
                    options.remove(i);
                }
                select.appendChild(new Option("Everyone", "Everyone", false, false))
                for (index in data.connected) {
                    name = data.connected[index]
                    select.appendChild(new Option(name, name, false, false))
                }
                if (selected in data.connected)
                    select.value = data.connected[selected];
                else
                    select.value = "Everyone"
                break;
            case "error":
                alert(data.error)      
        }
    }
    catch(err) {
        alert(err);
    }
}

function handleSend(socket) {
    var recipient = document.getElementById("recipient").value;
    var msgCtrl = document.getElementById("message")
    var message = msgCtrl.value;
    var verb = "private";
    if (recipient == "Everyone")
        verb = "broadcast"
    var msg = {
        to: recipient,
        msg: message,
        name: document.getElementById("fname").value,
        verb: verb
    }
    socket.send(JSON.stringify(msg));
    var prev = document.getElementById("sent_text").value
    document.getElementById("sent_text").value = recipient+'<< '+message+"\n" + prev
    msgCtrl.value = ""
}
