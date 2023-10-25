import socket
import os
import json
import time
import pickle
import threading
import sys

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

class ChatClient:
    def __init__(self, name="", registeredUsers=dict(), is_ACK_c=False, waitFor="", is_ACK_s=False, mode="normal", group="", serverIP="",
                 serverPort=0, clientPort=0, messageQueue=[], semaphore=threading.Semaphore(1)):
        self.name = name #required client nickname
        self.registeredUsers = registeredUsers 
        self.is_ACK_c = is_ACK_c
        self.is_ACK_s = is_ACK_s
        self.waitFor = waitFor
        self.mode = mode
        self.group = group
        self.serverIP = serverIP #required server-ip
        self.serverPort = serverPort #required server-port
        self.clientPort = clientPort #required client-port
        self.messageQueue = messageQueue # store msg from other clients when in a group chat. when leaving a group, display these msgs
        self.semaphore = semaphore
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        msg = package(header="connect", senderPort=self.clientPort, senderName=self.name)
        self.client_socket.sendto(pickle.dumps(msg), (self.serverIP, self.serverPort))
        self.listen_socket.bind(('', self.clientPort))
        listen = threading.Thread(target=self.clientListen, args=()) # start listening thread
        listen.start() 
        time.sleep(0.5)
        self.sendCommands() # start receiving commands

    def sendCommands(self):
        '''Receiving commands: reg; send <receiver-name> <msg>; dereg <name>; 
        create_group <group-name>; list_groups; join_group <group-name>; 
        send_all <msg>; list_members; leave_group'''
        while True:
            try:
                inputList = []
                try:
                    if self.mode == "normal":
                        tmp = input(">>> ")
                        inputList = tmp.split()
                    else:
                        tmp = input(f">>> ({self.group}) ")
                        inputList = tmp.split()
                except KeyboardInterrupt:
                    # tmp = []
                    # tmp.append("dereg")
                    # tmp.append(self.name)
                    # self.inputDereg(tmp) # delete
                    os._exit(1) 
                if len(inputList) == 0:
                    # break
                    continue
                header = inputList[0]
                if not self.validHeader(header):
                    continue
                if header == 'reg': # register
                    self.inputReg(inputList)
                elif header == 'send': # send message to a client
                    self.inputSend(inputList)
                elif header == 'dereg': # deregister
                    self.inputDereg(inputList)
                elif header == 'create_group': # create a group
                    self.inputCreateGroup(inputList)
                elif header == 'list_groups': # list all groups
                    self.inputListGroups(inputList)
                elif header == 'join_group': # join a specific group
                    self.inputJoinGroup(inputList)
                elif header == 'send_all': # send message to all group members
                    self.inputSendGroup(inputList)
                elif header == 'list_members': # list all group members
                    self.inputListMembers(inputList)
                elif header == 'leave_group': # leave a group
                    self.inputLeaveGroup(inputList)
                else:
                    self.display("[Invalid input!]")
            except:
                self.display("[Invalid input!]")

    def clientListen(self):
        while True:
            buffer, senderAddr = self.listen_socket.recvfrom(4096)
            message = pickle.loads(buffer)
            message.senderIP = senderAddr[0]
            header = message.header
            if header == 'update': # update register-table
                self.listenUpdate(message)
            elif header == 'register': # receive register result
                self.listenRegister(message)
            elif header == 'send': # receive message from other clients
                self.listenSend(message)
            elif header == 'ack': # receive ack from other clients
                self.listenClientAck(message)
            elif header == 'ack-create-group': # receive ack of the command "create_group"
                self.listenCreateGroupAck(message)
            elif header == 'ack-groups-result': # receive ack of the command "list_groups"
                self.listenGroupsResultAck(message) 
            elif header == 'ack-join-group': # receive ack of the command "join_group"
                self.listenJoinGroupAck(message)
            elif header == 'ack-group': # receive group messages
                self.listenGroupAck(message)
            elif header == 'member-result': # receive ack of the command "list_members"
                self.listenMemberResult(message)
            elif header == 'ack-leave-group': # # receive ack of the command "leave_group"
                self.listenLeaveGroup(message)
            elif header == 'ack-dereg': # receive ack of the command "dereg"
                self.is_ACK_s = True
            elif header == 'offline': # receive ack of the server receiving an offline message
                self.listenServerAck(message)
            elif header == 'recover-msg': # receive and recover offline messages
                self.listenRecoverMsg(message)
            elif header == 'ack-recovered': # receive an ack of the server has sent offline messages from this client to the receivers
                self.display(message.message)
            else:
                self.display("[Unkonwn header.]")

    def inputReg(self, inputList):
        msg = package(header="connect", senderPort=self.clientPort, senderName=self.name)
        self.client_socket.sendto(pickle.dumps(msg), (self.serverIP, self.serverPort))
        self.display("[Welcome back!]")

    def sendOfflineMessage(self, inputList):
        msg = ""
        for i in range(2, len(inputList)):
            msg = msg + inputList[i] + " "
        t = time.time()
        struct_time = time.localtime(t)
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', struct_time)
        message = package(header="offline", senderPort=self.clientPort, senderName=self.name, receiverName=inputList[1], message=msg, value=formatted_time)
        self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
        # self.display("[The client is offline. Message has been sent to the server.]")
        time.sleep(0.5)
        if self.is_ACK_s:
            self.display(f"[Offline message sent at {formatted_time} received by the server and saved.]")
            self.is_ACK_s = False
        else:
            if not self.retryFiveTimes(message):
                self.loseConnection()
                os._exit(1)

    def inputSend(self, inputList):
        receiverName = inputList[1]
        if receiverName in self.registeredUsers:
            if self.registeredUsers[receiverName][2] != "Online":
                self.sendOfflineMessage(inputList)
            else:
                msg = ""
                for i in range(2, len(inputList)):
                    msg = msg + inputList[i] + " "
                message = package(header="send", senderPort=self.clientPort, senderName=self.name, message=msg)
                self.waitFor = receiverName
                self.client_socket.sendto(pickle.dumps(message), (self.registeredUsers[receiverName][0], self.registeredUsers[receiverName][1]))
                # self.display("Message sent.")
                time.sleep(0.5)
                if self.is_ACK_c:
                    self.display(f"[Message received by {receiverName}.]")
                    self.is_ACK_c = False
                else:
                    self.display(f"[No ACK from {receiverName}, message sent to server.]")
                    self.notifyServer(receiverName)
                    self.sendOfflineMessage(inputList)
        else:
            self.display("[User does not exist.]")

    def inputDereg(self, inputList):
        if inputList[1] == self.name:
            message = package(header="dereg", senderPort=self.clientPort, senderName=self.name)
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
                self.display("[You are offline. Bye.]")
                # os._exit(1)
                return
            else:
                if not self.retryFiveTimes(message):
                    self.loseConnection()
                    os._exit(1)
        else:
            self.display("[Incorrect username!]")

    def inputCreateGroup(self, inputList):
        if self.mode == "normal":
            groupName = inputList[1]
            message = package(header="create_group", senderPort=self.clientPort, senderName=self.name, value=groupName)
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
            else:
                if not self.retryFiveTimes(message):
                    self.loseConnection()
                    os._exit(1)
        else:
            self.display("[You are already in a group chat room.]")

    def inputListGroups(self, inputList):
        if self.mode == "normal":
            message = package(header="list_groups", senderPort=self.clientPort, senderName=self.name)
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
            else:
                if not self.retryFiveTimes(message):
                    self.loseConnection()
                    os._exit(1)
        else:
            self.display("[You can not view all groups while in a group].")

    def inputJoinGroup(self, inputList):
        if self.mode == "normal":
            groupName = inputList[1]
            message = package(header="join_group", senderPort=self.clientPort, senderName=self.name, value=groupName)
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
            else:
                if not self.retryFiveTimes(message):
                    self.loseConnection()
                    os._exit(1)
        else:
            self.display("[You are already in a group.]")

    def inputSendGroup(self, inputList):
        if self.mode == "inGroup":
            msg = ""
            for i in range(1, len(inputList)):
                msg = msg + inputList[i] + " "
            t = time.time()
            struct_time = time.localtime(t)
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', struct_time)
            message = package(header="send_all", senderPort=self.clientPort, senderName=self.name, message=msg, value=self.group, content=formatted_time)
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
                self.display("[Group message received by server.]")
            else:
                if not self.retryFiveTimes(message):
                    self.loseConnection()
                    os._exit(1)
        else:
            self.display("[You are not in a group.]")

    def inputListMembers(self, inputList):
        if self.mode == "inGroup":
            message = package(header="list_members", senderPort=self.clientPort, senderName=self.name, value=self.group)
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
            else:
                if not self.retryFiveTimes(message):
                    self.loseConnection()
                    os._exit(1)
        else:
            self.display("[You are not in a group.]")

    def inputLeaveGroup(self, inputList):
        if self.mode == "inGroup":
            message = package(header="leave_group", senderPort=self.clientPort, senderName=self.name, value=self.group)
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
                self.releaseMessageQueue()
            else:
                if not self.retryFiveTimes(message):
                    self.loseConnection()
                    os._exit(1)
        else:
            self.display("[You have not joined a group yet.]")

    def listenUpdate(self, message):
        msg = message.content
        msg = json.loads(msg)
        self.registeredUsers = msg
        self.display("[Client table updated.]")
        # print(self.registeredUsers)

    def listenRegister(self, message):
        state = message.state
        if state == 'Online':
            self.display("[Welcome, You are registered.]")
        else:
            self.display("[You have already login somewhere else.]")
            os._exit(1)

    def listenSend(self, message):
        msg = message.message
        senderName = message.senderName
        if self.mode == "normal":
            self.display(f"{senderName}: "+msg)
            self.clientResponse(message.senderIP, message.senderPort)
        else:
            self.messageQueue.append(f"{senderName}: "+msg)
            self.clientResponse(message.senderIP, message.senderPort)

    def listenClientAck(self, message):
        senderName = message.senderName
        if senderName == self.waitFor:
            msg = message.message
            self.is_ACK_c = True
            # self.display(f"Message received by {senderName}.")

    def listenServerAck(self, message):
        if message.value == False:
            self.display(f"[Client {message.receiverName} exists!!]")
        self.is_ACK_s = True

    def listenCreateGroupAck(self, message):
        self.is_ACK_s = True
        value = message.value
        groupName = message.message
        if value == "approve":
            self.display(f"[Group {groupName} created by Server.]")
        else:
            self.display(f"[Group {groupName} already exists.]")

    def listenGroupsResultAck(self, message):
        self.is_ACK_s = True
        groupNames = json.loads(message.content)
        self.display("[Available Group Chats:]")
        for group in groupNames:
            self.display(f"{group}")

    def listenJoinGroupAck(self, message):
        self.is_ACK_s = True
        value = message.value
        groupName = message.message
        if value == "approve":
            self.display(f"[Entered group {groupName} successfully.]")
            self.group = groupName
            self.mode = "inGroup"
        else:
            self.display(f"[{groupName} does not exist.]")

    def listenGroupAck(self, message):
        senderName = message.senderName
        msg = message.message
        if senderName == self.name:
            self.is_ACK_s = True
        else:
            self.clientResponseGroup(self.serverIP, self.serverPort)
            self.display(f"[Group Message {senderName}: {msg}]")
            
    def listenMemberResult(self, message):
        self.is_ACK_s = True
        members = json.loads(message.content)
        self.display(f"[Members in group {self.group}:]")
        for member in members:
            self.display(f"[{member}]")

    def listenLeaveGroup(self, message):
        self.is_ACK_s = True
        self.display(f"[Leave group chat {self.group}.]")
        self.group = ""
        self.mode = "normal"

    def listenRecoverMsg(self, message):
        self.display("[You have offline messages:]")
        msgList = json.loads(message.content)
        for msg in msgList:
            self.display(f"{msg[1]}: {msg[2]} {msg[3]}")
        ack = package(header="ack-offlineMsg", message="An ACK.", senderName=self.name)
        self.client_socket.sendto(pickle.dumps(ack), (self.serverIP, self.serverPort))

    def display(self, msg):
        if self.mode == "normal":
            print("\r>>> "+msg)
        else:
            print(f"\r>>> ({self.group}) "+msg)   

    def clientResponse(self, senderIP, senderPort):
        ack = package(header="ack", serverPort=self.serverPort, senderName=self.name, message=f"This is an ACK from {self.name}.")
        self.client_socket.sendto(pickle.dumps(ack), (senderIP, senderPort))

    def clientResponseGroup(self, serverIP, serverPort):
        ack = package(header="ack-group", serverPort=self.serverPort, senderName=self.name, message=f"This is an ACK from {self.name}.")
        self.client_socket.sendto(pickle.dumps(ack), (serverIP, serverPort))

    def notifyServer(self, receiverName):
        message = package(header="notify", serverPort=self.serverPort, senderName=self.name, receiverName=receiverName)
        self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
    
    def validHeader(self, header):
        if self.mode == "normal":
            if header in ["reg", "send", "dereg", "create_group", "list_groups", "join_group"]:
                return True
        else:
            if header in ["reg", "send_all", "list_members", "leave_group", "dereg"]:
                return True
        self.display("Invalid command!")
        return False
    
    def retryFiveTimes(self, message):
        for i in range(5):
            self.client_socket.sendto(pickle.dumps(message), (self.serverIP, self.serverPort))
            self.display(f"[Message sent! {i+1} times. Retrying...]")
            time.sleep(0.5)
            if self.is_ACK_s:
                self.is_ACK_s = False
                return True
        return False
    
    def loseConnection(self):
        self.display("[Server not responding.]")
        self.display("[Exiting...]")

    def releaseMessageQueue(self):
        for msg in self.messageQueue:
            self.display(msg)

    def isOnline(self):
        if self.registeredUsers[self.name] == "Offline":
            self.display("[You are offline. Please register first.]")
            return False
        else:
            return True
        

class ChatServer:
    def __init__(self, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('localhost', port))
        self.regTable = dict()  # To store client info: {nickname: [IP, port, state]}
        self.groupList = dict()
        self.ackCand = dict()
        self.offlineMsg = list() #[[name, sender, timestamp, msg]]


    def start(self):
        print(f">>> [Server started at {self.server_socket.getsockname()[0]} on port {self.server_socket.getsockname()[1]}]")
        while True:
            try:
                print("[Start listening...]")
                data, addr = self.server_socket.recvfrom(4096)
                message = pickle.loads(data)
                message.senderIP = addr[0]
            except KeyboardInterrupt:
                self.server_socket.close()
                os._exit(1)
            self.analyzeMessage(message)

    def analyzeMessage(self, message):
        header = message.header
        clientIP = message.senderIP
        clientPort = message.senderPort
        clientName = message.senderName
        receiverName = message.receiverName
        value = message.value
        if header == 'connect':
            self.registerClient(clientIP, clientName, clientPort)
        elif header == 'notify':
            self.notify(receiverName)
        elif header == 'dereg':
            self.notify(clientName)
            self.serverDereg(clientIP, clientPort)
        elif header == 'create_group':
            self.createGroup(value, clientIP, clientPort)
        elif header == 'list_groups': # not required
            self.listGroups(clientName, clientIP, clientPort)
        elif header == 'join_group':
            self.joinGroup(value, clientIP, clientPort, clientName)
        elif header == 'send_all':
            self.broadcastGroup(clientName, message.message, value, message.content)
            counting = threading.Thread(target=self.serverCounting, args=())
            counting.start() # not understand
        elif header == 'ack-group':
            self.ackCand[value] = 1
        elif header == 'list_members': # not required
            self.listMembers(clientName, clientIP, clientPort, value)
        elif header == 'leave_group':
            self.leaveGroup(value, clientName, clientIP, clientPort)
        elif header == 'leave':
            self.notify(clientName)
        elif header == 'offline':
            self.storeOfflineMessage(message)
        elif header == 'ack-offlineMsg':
            self.ackRecover(message)
        else:
            pass

    def registerClient(self, address, clientName, clientPort):
        if clientName in self.regTable.keys():
            if self.regTable[clientName][2] == "Offline":
                self.regTable[clientName][2] = "Online"
                msgList = []
                for i in self.offlineMsg:
                    if clientName == i[0]:
                        msgList.append(i)
                if len(msgList) != 0:
                    pk = package(header="recover-msg", content=json.dumps(msgList))
                    self.server_socket.sendto(pickle.dumps(pk), (address, clientPort))

            else:
                print(">>> [Duplicate Login Detected!]")
                pk = package(header="register", state="Offline")
                self.server_socket.sendto(pickle.dumps(pk), (address, clientPort))
                time.sleep(0.5)
        else:
            newClient = [address, clientPort, "Online"]
            self.regTable[clientName] = newClient
            print(">>> [Client table updated.]")
            pk = package(header="register", state="Online")
            self.server_socket.sendto(pickle.dumps(pk), (address, clientPort))
            # self.server_socket.sendto(f"header:\nregister\nstate\n{True}".encode(), (address, clientPort)) #not understand
        self.broadcast()

    def notify(self, clientName):
        self.regTable[clientName][2] = "Offline"
        print(">>> [Client table updated.]")
        self.broadcast()

    def serverDereg(self, clientIP, clientPort):
        ack = package(header="ack-dereg", message="This is an ACK.")
        self.server_socket.sendto(pickle.dumps(ack), (clientIP, clientPort))
        print(">>> [ACK Sent.]")

    def createGroup(self, value, clientIP, clientPort):
        if value in self.groupList:
            ack = package(header="ack-create-group", value="deny", message=value)
        else:
            self.groupList[value] = list()
            ack = package(header="ack-create-group", value="approve", message=value)
        self.server_socket.sendto(pickle.dumps(ack), (clientIP, clientPort))
        print(">>> [ASK Sent.]")

    def listGroups(self, clientName, clientIP, clientPort):
        print(f">>> [Client {clientName} requests listing groups:]")
        group_names = []
        for key in self.groupList.keys():
            print(f">>> [{key}]")
            group_names.append(key)
        pk = package(header="ack-groups-result", content=json.dumps(group_names))
        self.server_socket.sendto(pickle.dumps(pk), (clientIP, clientPort))
        print(">>> [ACK Sent.]")

    def joinGroup(self, value, clientIP, clientPort, clientName):
        if value in self.groupList:
            ack = package(header="ack-join-group", value="approve", message=value)
            self.server_socket.sendto(pickle.dumps(ack), (clientIP, clientPort))
            print(">>> [ACK Sent.]")
            self.groupList[value].append(clientName)
            print(f">>> [Client {clientName} Joined Group {value}.]")
            print(f">>> [The current group chats info are: {self.groupList}]")
        else:
            ack = package(header="ack-join-group", value="deny", message=value)
            self.server_socket.sendto(pickle.dumps(ack), (clientIP, clientPort))
            print(">>> [ACK Sent.]")
            print(f">>> [Client {clientName} joining group {value} failed, group does not exist.]")

    def broadcast(self):
        for client in self.regTable.keys():
            if self.regTable[client][2] == "Online":
                pk = package(header="update", content=json.dumps(self.regTable))
                self.server_socket.sendto(pickle.dumps(pk), (self.regTable[client][0], self.regTable[client][1]))
                
    def broadcastGroup(self, senderName, message, groupNum, timestamp):
        ack = package(header="ack-group", senderName=senderName, message=message)
        if len(self.groupList) == 0:
            self.server_socket.sendto(pickle.dumps(ack), (self.regTable[senderName][0], self.regTable[senderName][1]))
            return
        for client in self.groupList[groupNum]:
            if(self.regTable[client][2] == "Online"):
                self.server_socket.sendto(pickle.dumps(ack), (self.regTable[client][0], self.regTable[client][1]))
                if client != senderName:
                    self.ackCand[client] = 0
            else:
                m = []
                m.append(client)
                m.append("Group Chat " + senderName)
                m.append(timestamp)
                m.append(message)
                self.offlineMsg.append(m)
        print(f">>> [Client {senderName} sent group message to group {groupNum}, message is {message}]")

    def serverCounting(self):
        time.sleep(0.5)
        for key, value in self.ackCand.items():
            if value == 0:
                self.groupList[value].remove(key)
                print(f">>> [Client {key} not responsive, removed from group {value}.]")
        self.ackCand = dict()
    
    def listMembers(self, clientName, clientIP, clientPort, value):
        print(f">>> [Client {clientName} requested listing members of group {value}:]")
        members = []
        for member in self.groupList[value]:
            print(f">>> [{member}]")
            members.append(member)
        ack = package(header="member-result", content=json.dumps(members))
        self.server_socket.sendto(pickle.dumps(ack), (clientIP, clientPort))
        print(">>> [ACK Sent.]")

    def leaveGroup(self, value, clientName, clientIP, clientPort):
        self.groupList[value].remove(clientName)
        print(f">>> [Client {clientName} left group {value}]")
        print(f">>> [The current group chats info are: {self.groupList}]")
        ack = package(header="ack-leave-group", message="This is a ACK")
        self.server_socket.sendto(pickle.dumps(ack), (clientIP, clientPort))
        print(">>> [ACK Sent.]")
    
    def storeOfflineMessage(self, message):
        receiverName = message.receiverName
        if self.regTable[receiverName][2] == "Online":
            isErr = False
            self.broadcast()
            msg = package(header="send", senderPort=message.senderPort, senderName=message.senderName, receiverName=message.receiverName, message=message.message)
            self.server_socket.sendto(pickle.dumps(msg), (self.regTable[message.receiverName][0], self.regTable[message.receiverName][1]))
        else:
            isErr = True
            m = []
            m.append(receiverName)
            m.append(message.senderName)
            m.append(message.value)
            m.append(message.message)
            self.offlineMsg.append(m)
        senderName = message.senderName
        ack = package(header="offline", receiverName=receiverName, message="This is an ACK.", value=isErr)
        self.server_socket.sendto(pickle.dumps(ack), (self.regTable[senderName][0], self.regTable[senderName][1]))
        print(">>> [ACK sent.]")

    def ackRecover(self, message): # when receive the ack of the recover msg from clients
        senderName = message.senderName
        ackList = list()
        ack = package(header="ack-recovered")
        for msg in self.offlineMsg:
            if msg[0] == senderName:
                name = msg[1]
                l = msg[1].split(" ")
                if len(l) > 1:
                    name = l[2]
                if self.regTable[name][2] == "Online":
                    ack.message = f"Offline Message sent at {msg[2]} received by {msg[0]}"
                    self.server_socket.sendto(pickle.dumps(ack), (self.regTable[name][0], self.regTable[name][1]))
                else:
                    tmp = []
                    tmp.append(name)
                    tmp.append(senderName)
                    timestamp = time.time()
                    struct_time = time.localtime(timestamp)
                    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', struct_time)
                    tmp.append(formatted_time)
                    tmp.append(f"Offline Message sent at {msg[2]} received by {msg[0]}")
                    self.offlineMsg.append(tmp)
        self.offlineMsg = [x for x in self.offlineMsg if x[0]!=senderName]


def checkIp(ip):
    if ip == "localhost":
        return True
    if len(ip.split(".")) != 4:
        return False
    for x in ip.split("."):
        if not x.isnumeric():
            return False
    return True

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "-s":
        port = int(sys.argv[2])
        if 1024 <= port <= 65535:
            server = ChatServer(port)
            server.start()
        else:
            print(">>> [Invalid port. Ensure the port is between 1024 and 65535.]")
            os._exit(1)
    elif mode == "-c":
        clientName = sys.argv[2]
        serverIP = sys.argv[3]
        serverPort = int(sys.argv[4])
        clientPort = int(sys.argv[5])
        if serverPort < 1024 or serverPort > 65535:
            print(">>> [Invalid server-port. Ensure the server-port is between 1024 and 65535.]]")
            os._exit(1)
        if clientPort < 1024 or clientPort > 65535:
            print(">>> [Invalid client-port. Ensure the client-port is between 1024 and 65535.]]")
            os._exit(1)
        if not checkIp(serverIP):
            print(">>> [Invalid server-ip!]")
            os._exit(1)
        client = ChatClient(name=clientName, serverIP=serverIP, serverPort=serverPort, clientPort=clientPort)
        client.start()
    elif mode == "-h":
        print(">>> [Server mode: python ChatApp.py -s <port>] \n>>> [Client mode: python ChatApp.py -c <name> <server-ip> <server-port> <client-port>]")
    else:
        print(">>> [Invalid mode. Please use '-c' as client mode or '-s' as server mode.]")
