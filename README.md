# ChatApp

Name: Wenbo Liu

UNI: wl2927

## 1. Introduction

It is a simple chat app writing in Python3.9 and based on UDP protocol. It support chatting, group chat and offline messages recoverment. All the messages have acknowledgement. You can try it out easily under the guidance.



## 2. How to use

Install all the required Python packages:

```
pip install -r requirements.txt
```

See the help of the commands:

```
python ChatApp.py -h
```

To start the server mode: 

````
python ChatApp.py -s <server-port>
````

To start the client mode: 

````
python ChatApp.py -c <client-name> <server-ip> <server-port> <client-port>
````

The port number should be in [1024, 65535].



## 3. Message package

The ```Class package``` is used to transfer messages between server-client or client-client. The most important attribute in the class is `header`. Both the server and the client used `header` to identify what is the next step when receiving a package. There are many other attributes like `serverIP` used to store the IP address of the server, `serverPort` stores the port number of the server, `message` used to store the message sent by the server or the client,`content` used to store some data structures, like a `dict()`. The whole class is shown as following:

```python
class package:
    def __init__(self, serverIP="", serverPort=0, senderIP="", senderPort=0, senderName="", 
                 receiverIP="", receiverPort=0, receiverName="", state="", header="", 
                 message="", content="", value=""):
        self.serverIP = serverIP # server-ip
        self.serverPort = serverPort # server-port
        self.senderIP = senderIP 
        self.senderPort = senderPort
        self.senderName = senderName
        self.receiverIP = receiverIP
        self.receiverPort = receiverPort
        self.receiverName = receiverName
        self.state = state # used to store the state of a client
        self.header = header
        self.message = message
        self.content = content
        self.value = value
```

 When transfer the package, I use `pickle.dumps(package)` to serialize the package and when receiving a package, I use `pickle.loads(package)` to unserialize. Besides, when transfer a `dict()`, like the register-table of the server, I will let `package.content = json.dumps(dict())` and use `json.loads(dict())` when receive a package content a dictionary.



## 4. ChatClient

### 4.1 init

When initialize a new `ChatClient` class, we need four parameters: `client-name`, `server-IP`, `server-Port` and `client-Port`. 

Set `is_ACK_c` ,  `is_ACK_s` to `False` and  `mode` to `normal`. 

Define two sockets: `self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM), self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)`

### 4.2 start()

Send a package with `header='connect'` to the server. 

Start listening-thread and `sendCommand()`.

### 4.3 sendCommands()

Has some APIs.

#### 4.3.1 reg

Format: 

```reg
reg
```

In both mode

`self.inputReg()` The function will send a package with `header='connect'` to the server to register.

#### 4.3.2 send

Format:

```
send <client-name> <message>
```

In `normal` mode

`self.inputSend()` The function will send the offline message to the server if the client is offline. If the client is online, the function will send the message to the client directly, by using a package with `header='send'`. After sending the package, the function will wait for the ACK. If the `client-name` is not exiting, it will display '[User does not exist.]'.

#### 4.3.3 dereg

Format:

```
dereg <client-name>
```

In both mode

`self.inputDereg()` The function will send a package with `header='dereg'` to the server to deregister and wait for the ACK from the server. If it does not receive an ACK, it will try five times.

#### 4.3.4 create_group

Format:

```
create_group <group-name>
```

In `normal` mode

`self.inputCreateGroup()` The function will send a package with `header='create_group'` to the server in order to great a group in the server. It will also wait for the ACK from the server and try five times if not receives an ACK.

#### 4.3.5 list_groups

Format: 

````
list_groups
````

In `normal` mode

`self.inputListGroups()` The function will send a package with `header='list_groups'` to the server and try five times if not receives an ACK. If the client is not in the `normal` mode, it will display '[You can not view all groups while in a group].'.

#### 4.3.6 join_group

Format: 

````
join_group <group-name>
````

In `normal` mode

`self.inputJoinGroup()` The function will send a package with `header='join_group'` to the server, wait for the ACK and try five times if not receives an ACK. It will display '[You are already in a group.]' if the client is not in the `normal` mode.

#### 4.3.7 send_all

Format: 

````
send_all <message>
````

In `inGroup` mode

`self.inputSendGroup()` The function will send the message to the server through a package, wait for an ACK and try five times if not receives an ACK. If the client is not in the `inGroup` mode, it will display '[You are not in a group.]'.

#### 4.3.8 list_members

Format: 

````
list_members
````

In `inGroup` mode

`self.inputListMembers()` The function will send a package to the server to ask for group members. It will wait for the ACK and try five times if not receives an ACK. If the client is not in the `inGroup` mode, it will display '[You are not in a group.]'.

#### 4.3.9 leave_group

Format: 

````
leave_group
````

In `inGroup` mode

`self.inputLeaveGroup()` the function will tell the server the client wants to leave the group. It will wait for an ACK from the server and retry fime times if not receives an ACK.

### 4.4 clientListen()

```python
buffer, senderAddr = self.listen_socket.recvfrom(4096)
message = pickle.loads(buffer)
message.senderIP = senderAddr[0]
header = message.header
```

Use header to identify the next step.

#### 4.4.1 update

`self.listenUpdate()`: Update the register-table of the client.

#### 4.4.2 register

`self.listenRegister()` : Register the client.

#### 4.4.3 send

`self.listenSend()`: If the client is not in `inGroup` mode, it will display the message to the client. Otherwise, it will store the message to `self.messageQueue`.

#### 4.4.4 ack

`self.listenClientAck()`: Receive the ACK from another client.

#### 4.4.5 ack-create-group

`self.listenClientAck()`: Receive the ACK of the `create_group` command. If the value of the package is 'approve', the server has create a group successfully. Otherwise, failed.

#### 4.4.6 ack-groups-result

`self.listenGroupsResultAck()`: Receive the ACK of the `list_groups` command. Display all the group name.

#### 4.4.7 ack-join-group

`self.listenJoinGroupAck()`: Receive the ACK of the `join_group` command. If the value of the package is 'approve', the client has joined a group successfully. Otherwise, failed.

#### 4.4.8 ack-group

`self.listenGroupAck()`: Receive and display group messages.

#### 4.4.9 member-result

`self.listenMemberResult()`: Receive and display all members in the group.

#### 4.4.10 ack-leave-group

`self.listenLeaveGroup()`: Receive the ACK of leaving the group and set to `normal` mode.

#### 4.4.11 offline

`self.listenServerAck()`: If the value of the package is `False`, it means the receiver of the message is online, you should send the message to the client directly rather than sending to the server.

#### 4.4.12 recover-msg

`self.listenRecoverMsg()`: Display all offline messages of the client and send an ACK to the server.

#### 4.4.13 ack-recovered

Display that the offline messages have been sent to clients when they register again.`

### 4.5 display()

```python
def display(self, msg):
    if self.mode == "normal":
        print("\r>>> "+msg)
    else:
        print(f"\r>>> ({self.group}) "+msg) 
```

Display messages in a specific format.

### 4.6 validHeader()

```python
def validHeader(self, header):
        if self.mode == "normal":
            if header in ["reg", "send", "dereg", "create_group", "list_groups", "join_group"]:
                return True
        else:
            if header in ["reg", "send_all", "list_members", "leave_group", "dereg"]:
                return True
        self.display("Invalid command!")
        return False
```

Judge the `header`.

### 4.7 retryFiveTimes()

```python
def retryFiveTimes(self, message):
        for i in range(5):
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            self.display(f"[Message sent! {i+1} times. Retrying...]")
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
                return True
        return False
```

Retry five time every 0.5 seconds.



## 5. ChatServer

### 5.1 init

Define a socket, bind the `port` to the `localhost`. Initialize the `register-table`, `group-list`, `offline-messages`.

### 5.2 start()

Start the listening thread.

### 5.3 analyzeMessage()

Analyze the received package's header.

#### 5.3.1 connect

`self.registerClient()`: If the client has registered before, set the client to online state and send the offline messages to the client, else add the client to the register-table.

#### 5.3.2 dereg

`self.serverDereg(); self.notify()`: Set the client to offline state and broadcast the register-table to all clients. Send the ACK to the client.

#### 5.3.3 create_group

`self.createGroup():` If the group name has not been in the group list, add it to the list. 

#### 5.3.4 list_groups

`self.listGroups()`: Get all the group names as a list and send the list to the client.

#### 5.3.5 join_group

`self.joinGroup()`: Append the client to the specific group. If the group not exits, return false.

#### 5.3.6 send_all

`self.broadcastGroup()`: If the group member is online, send the message to him. If the member is offline, store the message on server.

#### 5.3.7 list_members

`self.listMembers()`: If the client is `inGroup` mode, send all group members' name to the client.

#### 5.3.8 leave_group

`self.leaveGroup()`: Remove the client from his group and send an ACK to the server.

#### 5.3.9 leave

`self.notify()`: Set the client offline and broadcast to all the other clients.

#### 5.3.10 offline

`self.storeOfflineMessage()`: If the receiver is online, send the message to the receiver and broadcast the latest register-table. If the receiver is offline, store the message on the server.

#### 5.3.11 ack-offlineMsg

`self.ackRecover()`: When receives the ack of the recover messages from clients, if the messages' senders are online, send an ACK to them, else store the ACK and send the ACKs to the clients when they are online.

### 5.4 broadcast()

Send the latest register-table to all the online clients.



## 6. Tests

### Case 1:

```
1. start server
2. start client x(the table should be sent from server to x)
3. start client y(the table should be sent from server to x and y)
4. start client z(the table should be sent from server to x and y and z)
5. chat x->y, y->z, ... , x ->z (All combinations)
6. dereg x
7. chat y->x (message should be sent to server to be saved)
8. chat z->x (same as above)
9. reg x (x’s status has to be broadcasted to all the other clients, messages should be sent from server to x, and
y, z should display delivery notification)
10. x, y, z : exit
```

### Output 1:

#### Server:

```
python ChatApp.py -s 2475
>>> [Server started at 127.0.0.1 on port 2475]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
>>> [ACK Sent.]
[Start listening...]
>>> [ACK sent.]
[Start listening...]
>>> [ACK sent.]
[Start listening...]
[Start listening...]
[Start listening...]
```

#### c1 (x):

```
python ChatApp.py -c c1 127.0.0.1 2475 2927
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
send c2 from c1
>>> [Message received by c2.]
>>> send c3 from c1
>>> [Message received by c3.]
>>> c2: from c2 
>>> c3: from c3 
dereg c1
>>> [You are offline. Bye.]
>>> reg
>>> [Welcome back!]
>>> [You have offline messages:]
>>> c2: 2023-10-25 14:40:07 test offline msg 
>>> c3: 2023-10-25 14:40:22 test offline msg from c3 
>>> [Client table updated.]
```

#### c2 (y):

```
python ChatApp.py -c c2 localhost 2475 2928
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> c1: from c1 
send c1 from c2
>>> [Message received by c1.]
>>> send c3 from c3 
>>> [Message received by c3.]
>>> c3: from c3 
>>> [Client table updated.]
send c1 test offline msg
>>> [Offline message sent at 2023-10-25 14:40:07 received by the server and saved.]
>>> [Client table updated.]
>>> Offline Message sent at 2023-10-25 14:40:07 received by c1
```

#### c3 (z):

```
python ChatApp.py -c c3 localhost 2475 2929
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> c1: from c1 
>>> c2: from c3 
send c1 from c3
>>> [Message received by c1.]
>>> send c2 from c3
>>> [Message received by c2.]
>>> [Client table updated.]
send c1 test offline msg from c3
>>> [Offline message sent at 2023-10-25 14:40:22 received by the server and saved.]
>>> [Client table updated.]
>>> Offline Message sent at 2023-10-25 14:40:22 received by c1
```



### Case 2:

```
1. start server
2. start client x (the table should be sent from server to x )
3. start client y (the table should be sent from server to x and y)
4. start client z (broadcast updated table the same way as above)
5. server exit
6. dereg y (dereg will fail, y should make 5 attempts, printing each attempt, and then exit)
7. send message x->z (should still work!!!)
```

### Outpute 2:

#### Server:

```
python ChatApp.py -s 2475
>>> [Server started at 127.0.0.1 on port 2475]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
^C%   
```

#### c1 (x):

```
python ChatApp.py -c c1 127.0.0.1 2475 2927
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
send c3 hello from c1
>>> [Message received by c3.]
>>> c3: hi from c3 
```

#### c2 (y):

```
python ChatApp.py -c c2 localhost 2475 2928
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
dereg c2
>>> [Message sent! 1 times. Retrying...]
>>> [Message sent! 2 times. Retrying...]
>>> [Message sent! 3 times. Retrying...]
>>> [Message sent! 4 times. Retrying...]
>>> [Message sent! 5 times. Retrying...]
>>> [Server not responding.]
>>> [Exiting...]
```

#### c3 (z):

```
python ChatApp.py -c c3 localhost 2475 2929
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> c1: hello from c1 
send c1 hi from c3
>>> [Message received by c1.]
```



### Case 3:

```
1. start server
2. start client x (the table should be sent from server to x )
3. start client y (the table should be sent from server to x and y)
4. start client z (the table should be sent from server to x , y and z)
5. start client a (the table should be sent from server to x , y, z, and a)
6. dereg a
7. send group message from x (y, z receive messages immediately, stored as an offline message for a)
8. send private message y->a (message should be sent to server to be saved).
9. reg a (a’s status has to be broadcasted to all the other clients, both messages should be sent from server to a,
and y should display the notification.)
```

### Output 3:

#### Server:

```
python ChatApp.py -s 2475
>>> [Server started at 127.0.0.1 on port 2475]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [ASK Sent.]
[Start listening...]
>>> [ACK Sent.]
>>> [Client c4 Joined Group g.]
>>> [The current group chats info are: {'g': ['c4']}]
[Start listening...]
>>> [ACK Sent.]
>>> [Client c3 Joined Group g.]
>>> [The current group chats info are: {'g': ['c4', 'c3']}]
[Start listening...]
>>> [ACK Sent.]
>>> [Client c2 Joined Group g.]
>>> [The current group chats info are: {'g': ['c4', 'c3', 'c2']}]
[Start listening...]
>>> [ACK Sent.]
>>> [Client c1 Joined Group g.]
>>> [The current group chats info are: {'g': ['c4', 'c3', 'c2', 'c1']}]
[Start listening...]
>>> [Client table updated.]
>>> [ACK Sent.]
[Start listening...]
>>> [Client c1 sent group message to group g, message is send_all Welcome from c1 ]
[Start listening...]
[Start listening...]
[Start listening...]
>>> [Client c2 left group g]
>>> [The current group chats info are: {'g': ['c4', 'c3', 'c1']}]
>>> [ACK Sent.]
[Start listening...]
>>> [ACK sent.]
[Start listening...]
[Start listening...]
[Start listening...]
```

#### c1 (x):

```
python ChatApp.py -c c1 127.0.0.1 2475 2927
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
join_group g
>>> [Entered group g successfully.]
>>> (g) [Client table updated.]
send_all Welcome from c1
>>> (g) [Group message received by server.]
>>> (g) [Client table updated.]
>>> (g) Offline Message sent at 2023-10-25 15:05:22 received by c4
```

#### c2 (y):

```
python ChatApp.py -c c2 localhost 2475 2928
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
join_group g
>>> [Entered group g successfully.]
>>> (g) [Client table updated.]
>>> (g) [Group Message c1: send_all Welcome from c1 ]
leave_group
>>> (g) [Leave group chat g.]
>>> send c4 hello from c2
>>> [Offline message sent at 2023-10-25 15:05:37 received by the server and saved.]
>>> [Client table updated.]
>>> Offline Message sent at 2023-10-25 15:05:37 received by c4
```

#### c3 (z):

```
python ChatApp.py -c c3 localhost 2475 2929
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
join_group g
>>> [Entered group g successfully.]
>>> (g) [Client table updated.]
>>> (g) [Group Message c1: send_all Welcome from c1 ]
>>> (g) [Client table updated.]
```

c4 (a):

```
python ChatApp.py -c c4 localhost 2475 2930
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> create_group g
>>> [Group g created by Server.]
>>> join_group g
>>> [Entered group g successfully.]
>>> (g) dereg c4
>>> (g) [You are offline. Bye.]
>>> (g) reg
>>> (g) [Welcome back!]
>>> (g) [You have offline messages:]
>>> (g) Group Chat c1: 2023-10-25 15:05:22 send_all Welcome from c1 
>>> (g) c2: 2023-10-25 15:05:37 hello from c2 
>>> (g) [Client table updated.]
```



### Case 4:

```
1. start server
2. start client x (the table should be sent from server to x )
3. start client y (the table should be sent from server to x and y)
4. start client z (the table should be sent from server to x, y, z)
5. dereg z
6. send private message x->z
7. send private message y->z 
8. dereg x
9. reg z (y should receive the ACK that the offline message has been sent to z while x should not)
10. reg x (x should receive the ACK that the offline message has been sent to z)
```

### Output 4:

#### Server:

```
python ChatApp.py -s 2475
>>> [Server started at 127.0.0.1 on port 2475]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
[Start listening...]
>>> [Client table updated.]
>>> [ACK Sent.]
[Start listening...]
>>> [ACK sent.]
[Start listening...]
>>> [ACK sent.]
[Start listening...]
>>> [Client table updated.]
>>> [ACK Sent.]
[Start listening...]
[Start listening...]
[Start listening...]
[Start listening...]
[Start listening...]
```

#### c1 (x):

```
python ChatApp.py -c c1 127.0.0.1 2475 2927
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
send c3 hi from c1
>>> [Offline message sent at 2023-10-25 15:21:11 received by the server and saved.]
>>> dereg c1
>>> [You are offline. Bye.]
>>> reg
>>> [Welcome back!]
>>> [You have offline messages:]
>>> c3: 2023-10-25 15:21:30 Offline Message sent at 2023-10-25 15:21:11 received by c3
>>> [Client table updated.]
```

#### c2 (y):

```
python ChatApp.py -c c2 localhost 2475 2928
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
send c3 hi from c2
>>> [Offline message sent at 2023-10-25 15:21:19 received by the server and saved.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> Offline Message sent at 2023-10-25 15:21:19 received by c3
>>> [Client table updated.]
```

#### c3 (z):

```
python ChatApp.py -c c3 localhost 2475 2929
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> dereg c3
>>> [You are offline. Bye.]
>>> reg
>>> [Welcome back!]
>>> [You have offline messages:]
>>> c1: 2023-10-25 15:21:11 hi from c1 
>>> c2: 2023-10-25 15:21:19 hi from c2 
>>> [Client table updated.]
>>> [Client table updated.]
>>> Offline Message sent at 2023-10-25 15:21:30 received by c1
```