import socket
import re

import gather

#debugging = True
debugging = False

class Bot:
    def __init__(self, server='irc.uk.quakenet.org', port=6667, channel='#wot-gathers', nick='phood-bot', Qpassword='8ehrkzCegS', realname = 'TEST GATHER BOT'):
        """creates the socket object and connects to the server"""

        self.server= server
        self.port = port
        self.channel = channel
        self.nick = nick
        self.Qpassword = Qpassword
        self.realname = realname
        self.authSent = False

        self.isConnected = False
        self.joinedChannel = False
        self.isAuthed = False
        self.isOpped = False
        self.modesChecked = False
        self.modesSet = False
        self.checkedNames = False

        self.nameList = []


        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc.connect( (server, port ) )
        self.data = self.irc.recv ( 4096 )

        self.gather = gather.channel(self)
        
    def nickname(self):
        self.write('NICK', [self.nick])
        #self.irc.send('NICK ' + self.nick + '\r\n')

        self.write('USER', [self.nick, 'test', self.server], self.realname)
        #self.irc.send('USER %s %s %s :%s\r\n' % (self.nick, 'test', self.server, self.realname))
        
    def join_channel(self):
        self.write('JOIN', [self.channel])
        #self.irc.send('JOIN ' + self.channel + '\r\n')
        self.joinedChannel = True

    def auth_me(self):
        if not self.authSent:
            self.write('AUTH', [self.nick, self.Qpassword])
            #self.irc.send('AUTH ' + self.nick + ' ' + self.Qpassword + '\r\n')
            self.authSent = True

    def checkModes(self):
        self.write('MODE', [self.channel])
        #self.irc.send('MODE %s \r\n' % self.channel)
        self.modesChecked = True

    def setModes(self):
        self.write('MODE', [self.channel, '+tnCNr'])
        #self.irc.send('MODE %s +tnCNrm \r\n' % self.channel)
        self.modesSet = True

    def colorise (self, input, txt=None, bg=None, otxt=None, obg=None):
        output = ''
        if txt is not None or bg is not None:
            output = '\x03'
            if txt is not None:
                output = output + str(txt)
                if bg is not None:
                    output = output + ',' + str(bg)
            if bg is not None and (txt is None):
                output = output + '1,'+str(bg)
        output = output + str(input)

        if txt is not None or bg is not None:
            output = output + '\x03'
            if otxt is not None or obg is not None:
                if otxt is not None:
                    output = output + str(otxt)
                    if obg is not None:
                        output = output + ',' + str(obg)
                if obg is not None and (otxt is None):
                    output = output + '1,'+str(obg)
        return output

    def sendChannelMsg(self, msg, txt=None, bg=None):
        if txt or bg:
            msg = self.colorise(msg, txt, bg, txt, bg)

        self.write('PRIVMSG', [self.channel], msg)

    def write(self, cmd=None, arguments=[], msg=None):
        sendstr = ""
        if cmd and len(arguments):
            sendstr = sendstr + str(cmd)
            for arg in arguments:
                sendstr = sendstr + " " + str(arg)
            if msg:
                sendstr = sendstr + " :"+str(msg)
            sendstr= sendstr + "\r\n"
            self.irc.send(sendstr)

    def handleResponse(self, match):
        user = match.group(1)
        host = match.group(2)
        cmd = match.group(3)
        channel = match.group(4)
        data = match.group(5)
        arguments = []
        msg = ""
        if data:
            datasp = data.split(":", 1)
            arguments = datasp[0].split(" ")
            if len(datasp) > 1:
                msg = datasp[1]

        arguments = filter(None, arguments)

        if debugging:
            print user, cmd, channel, arguments, msg

        if user:
            if channel == self.channel:
                if cmd == "PRIVMSG":
                    if msg.startswith("!"):
                        self.gather.takeCommand(user, msg)
                if cmd == "PART":
                    self.gather.userOff(cmd, user, msg)

                if cmd == "JOIN":
                    self.write('WHOIS', [user])

            if cmd == "QUIT":
                self.gather.userOff(cmd, user, msg)

            if cmd == "NICK":
                self.gather.userNick(user, msg)

        if user == "Q":
            if cmd == "NOTICE":
                if self.nick in arguments:
                    if msg == "You are now logged in as %s." % self.nick:
                        self.isAuthed = True
            if cmd == "MODE" and channel == self.channel:
                if "+o" in arguments and self.nick in arguments:
                    self.isOpped = True

        

    def handleSrvResponse(self, match):
        typ = int(match.group(2))
        user = match.group(3)
        data = match.group(4)

        arguments = []
        msg = ""
        if data:
            datasp = data.split(":", 1)
            arguments = datasp[0].split(" ")
            if len(datasp) > 1:
                msg = datasp[1]
        arguments = filter(None, arguments)

        if debugging:
            print typ, user, arguments, msg

        if typ == 221 and user == self.nick and "+i" in arguments:
            self.isConnected = True

        if typ == 353 and self.channel in arguments:
            self.namelist = []
            for usrname in msg.split(' '):
                if usrname.startswith(('+', '@')):
                    usrname = usrname[1:]
                self.nameList.append(usrname)
            self.gather.checkUsers()

        if typ == 330:
            self.gather.updateUser(arguments[1], arguments[0])
            print arguments[0] + ' is authed as: '+ arguments[1]

        if typ == 324 and self.channel in arguments:
            self.setModes()

    def work(self):
        data = self.irc.recv ( 4096 )    

        for line in data.split('\r\n'):

            if re.match(r'PING :(.*)', line):
                test = re.match(r'PING :(.*)', line)
                self.write('PONG', [test.group(1)])
                print "Replied to Server Ping"

            if re.match(r':([\S]+)!([\S]+) ([\S]+)[\s]?(#[\S]+)?[\s]?(.+)?', line):
                test = re.match(r':([\S]+)!([\S]+) ([\S]+)[\s]?(#[\S]+)?[\s]?(.+)?', line)
                self.handleResponse(test)


            elif re.match(r':([\S]+) ([\d]+) ([\S]+)(.+)?', line):
                test = re.match(r':([\S]+) ([\d]+) ([\S]+)(.+)?', line)
                self.handleSrvResponse(test)
            else:
                #print "bugger"
                #print line
                pass

            if self.isConnected:
                if not self.isAuthed:
                    self.auth_me()
                else:

                    #print "opped", self.isOpped
                    if not self.joinedChannel:
                        self.join_channel()
                    else:
                        if self.isOpped:
                            pass

bot = Bot()
bot.nickname()
while True:
    bot.work()
