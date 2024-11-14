var server = []
var user_global=[]
var file_global=[]

let btnLogin = document.querySelector('.btn_login')

let passwords = [];
let usernames = [];

class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            searchButton: document.querySelector('.search__button'),
            sendButton: document.querySelector('.send__button')
        }

        this.state = false;
        this.messages = [];
    }


    display() {
        const {openButton, chatBox, sendButton, searchButton} = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox))

        btnLogin.addEventListener('click', () => this.addUser());

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({key}) => {
            if (key === "Enter") {
                this.onSendButton(chatBox)
            }
        })
    }

    addUser(){

    /* document.querySelector('.chatbox__button').style.display = "block";*/
    var newUser = document.querySelector('.input_username').value;
    var newPass = document.querySelector('.input_password').value;
    var status = document.querySelector('.span_result');

    usernames = usernames.concat(newUser);
    passwords = passwords.concat(newPass);
    console.log(usernames);
    console.log(passwords);

    status.innerHTML = "";

    fetch(server+'/adduser', {
            method: 'POST',
            body: JSON.stringify({ user: newUser, pass: newPass }),
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json'
            },
          })
           .then(ack => ack.json())
           .then(ack => {
            if (ack == 'incomplete'){
               status.appendChild(document.createTextNode("Please fill up the necessary data!"))
            }
            if (ack == 'none'){
              status.appendChild(document.createTextNode("Welcome User " + newUser + "!"))
              document.querySelector('.chatbox__button').style.display = "block";
            }
            console.log(ack)
            textField.value = ''
        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox)
            textField.value = ''
          });

     user_global=newUser

    }

    toggleState(chatbox) {
        this.state = !this.state;

        // show or hides the box
        if(this.state) {
            this.updateChatText(chatbox,1);
            chatbox.classList.add('chatbox--active')
            fetch(server+'/ini', {
            method: 'POST',
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json'
            },
          })
          .then(r => r.json())
          .then(r => {
          let msg_ini = { name: "User", message: r.answer };
          this.messages.push(msg_ini);
          this.updateChatText(chatbox,0);
          textField.value = ''
          }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox,0)
            textField.value = ''
          });

        } else {
            chatbox.classList.remove('chatbox--active');
            /*for (let i = 0; i <= this.messages.length+100; i++) {
               this.messages.pop();
            }*/
            /*this.messages.pop();*/
            this.messages=[]; /* empty the array in an easier way */
            this.updateChatText(chatbox);
            textField.value = ''
        }
    }

    async onSendButton(chatbox) {
        var textField = chatbox.querySelector('input');
        let text1 = textField.value
        if (text1 === "") {
            return;
        }

        document.querySelector('.send__button').disabled = true;
        document.querySelector('.chatbox__support').disabled = true;
        chatbox.querySelector('input').disabled = true;

        let msg1 = { name: "User", message: "<b>" + user_global + '</b>: '+ text1 }

        this.messages.push(msg1);
        this.updateChatText(chatbox,1)


        await fetch(server+'/predict', {
            method: 'POST',
            body: JSON.stringify({ message: text1 }),
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json'
            },
          })
           .then(r => r.json())
           .then(r => {
            let msg2 = { name: "User", message: '<b>ShopBot</b>: ' + r.answer };
            this.messages.push(msg2);
            this.updateChatText(chatbox,0)
            textField.value = ''

            var imgEl = document.getElementById("img_input");

            imgEl.src = r.file_name;
            imgEl.style.display = "block";
            r.file_name
            document.querySelector('.send__button').disabled = false;
            document.querySelector('.chatbox__support').disabled = false;
            chatbox.querySelector('input').disabled = false;


        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox,0)
            textField.value = ''
          });
    }


    updateChatText(chatbox,sel) {
        var html = '';
        this.messages.slice().reverse().forEach(function(item, index) {
            if (item.name === "User")
            {
                html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>'
            }
            else
            {
                html += '<div class="messages__item messages__item--operator">' + item.message + '</div>'
            }
          });

         if (sel == 1)
         {
            html += '<div class="loading" style="position:absolute; left:25px; top:400px; color=#90EE90"><div class="circle circle-1"></div><div class="circle circle-2"></div><div class="circle circle-3"></div></div>'

         }

        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
    }
}

function getFileData() {

   file_global = this.files[0];

}

const toggleLoading=(show)=>loadingElement.classList.toggle("hide",show)

const chatbox = new Chatbox();
chatbox.display();
