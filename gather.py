import sqlite3 as lite
import sys


class channel(object):
    """docstring for channel"""
    def __init__(self, bot):
        super(channel, self).__init__()
        self.bot = bot
        self.userlist = userList()
        self.db = db()
        self.admins = ['phood', 'klutch']

    def checkUsers(self):
        for username in self.bot.nameList:
            self.bot.write('WHOIS', [username])

    def updateUser(self, auth, name):
        if not auth == 'Q':
            usr = self.userlist.findByAuth(auth)
            if not usr:
                usr = user(name)
                usr.authed = True
                usr.authedAs = auth
                self.userlist.userList.append(usr)
            self.db.getUser(usr)
            self.voice(usr)
    
    def voice(self, usr):
        if usr.authed:
            if usr.authedAs in self.admins:
                self.bot.write('PRIVMSG', ['Q'], 'CHANLEV ' + self.bot.channel + ' ' + usr.name + ' ' + '+o')
            elif usr.vouchedBy:
                self.bot.write('PRIVMSG', ['Q'],  'CHANLEV ' + self.bot.channel + ' ' + usr.name + ' ' + '+v')

    def takeCommand(self, usr, msg):
        if msg.find(' ') > 0:
            action, cmd = msg.split(' ', 1)
        else:
            action, cmd = (msg, '')
        usr = self.userlist.findByChannelName(usr)
        if usr:
            if action == "!vouch" and len(cmd) > 0:
                for usrname in cmd.split(' '):
                    vouchee = self.userlist.findByChannelName(usrname)
                    if vouchee:
                        self.vouch(usr, vouchee)

    def vouch(self, voucher, vouchee):
        if voucher.authed and (voucher.vouchedBy or (voucher.authedAs in self.admins)):
            if vouchee.authed and not vouchee.vouchedBy:
                vouchee.vouchedBy = voucher.dbID
                self.db.setUser(vouchee)
                self.voice(vouchee)
        

class userList(object):
    """docstring for userList"""
    def __init__(self):
        super(userList, self).__init__()
        self.userList=[]

    def findByChannelName (self, name):
        found = False
        for player in self.userList:
            if player.name == name:
                found = True
                return player
        if not found:
            return False

    def findByAuth (self, name):
        found = False
        for player in self.userList:
            if player.authedAs == name:
                found = True
                return player
        if not found:
            return False

    def findByWotUsername (self, name):
        found = False
        for player in self.userList:
            if player.wotUsername == name:
                found = True
                return player
        if not found:
            return False

class user(object):
    """docstring for user"""
    def __init__(self, name):
        super(user, self).__init__()
        self.name = name
        self.authed = False
        self.authedAs = None
        self.inGame = False
        self.vouchedBy = None
        self.dbID = None
        self.wotUsername = None
        self.tanks = "No listed tanks, please use !settanks <list of your tanks> to set this before playing a game."
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.eff = 0
        self.winsix = 0
        self.winrate = 0


class db(object):
    """docstring for db"""
    def __init__(self):
        super(db, self).__init__()
        self.con = None
        self.cur = None

        self.buildTables()
    
    def connect(self):
        try:
            self.con = lite.connect('main.db')
            self.con.row_factory = lite.Row         
            self.cur = self.con.cursor()

        except lite.Error, e:
            print "DATABASE ERROR!"
            sys.exit(1)

    def close(self):
        if self.con:
            self.con.close()

    def adduser(self, user):
        sqlinsert = "INSERT INTO users (name, authed, authedAs) VALUES ('"+str(user.name)+"', "+str(int(user.authed))+", '"+str(user.authedAs)+"');"
        self.connect()
        self.cur.execute(sqlinsert)
        self.con.commit()
        rowid = self.cur.lastrowid
        print rowid
        self.close()
        user.dbID = rowid

    def getUser(self, user):
        self.connect()
        if user.dbID:
            self.cur.execute("SELECT count(*) as num, * FROM 'users' WHERE idusers='"+user.dbID+"' LIMIT 0,1;")
            userexists = self.cur.fetchone()
            if userexists['num']:
                user.dbID = userexists[1]
        elif user.authed and user.authedAs:
            self.cur.execute("SELECT count(*) as num, * FROM 'users' WHERE authedAs='"+user.authedAs+"' LIMIT 0,1;")
            userexists = self.cur.fetchone()
            if userexists['num'] == 0:
                self.adduser(user)
            else:
                user.inGame = userexists['inGame']
                user.vouchedBy = userexists['vouchedBy']
                user.dbID = userexists['idusers']
                user.wotUsername = userexists['wotUsername']
                user.tanks = userexists['tanks']
                user.wins = userexists['wins']
                user.losses = userexists['losses']
                user.draws = userexists['draws']
                user.eff = userexists['eff']
                user.winsix = userexists['winsix']
                user.winrate = userexists['winrate']
        self.close()

    def setUser(self, user):
        self.connect()
        if user.dbID:
            self.cur.execute("UPDATE 'users' SET name='" + str(user.name) + "', authed='" + str(user.authed) + "', authedAs='" + str(user.authedAs) + "', inGame='" + str(user.inGame) + "', vouchedBy='" + str(user.vouchedBy) + "', wotUsername='" + str(user.wotUsername) + "', tanks='" + str(user.tanks) + "' WHERE idusers='" + str(user.dbID)+"'")
            self.con.commit()
        self.close()


    def buildTables(self):

        self.connect()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS `users` (
  "idusers" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "name" TEXT,
  "authed" INTEGER DEFAULT 0,
  "authedAs" TEXT,
  "vouchedBy" INT,
  "inGame" INTEGER DEFAULT 0,
  "wotUsername" TEXT,
  "tanks" TEXT,
  "wins" INTEGER DEFAULT 0,
  "losses" INTEGER DEFAULT 0,
  "draws" INTEGER DEFAULT 0,
  "eff" INTEGER DEFAULT 0,
  "winsix" INTEGER DEFAULT 0,
  "winrate" INTEGER DEFAULT 0);""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS "games" (
  "idgames" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "status" INTEGER,
  "date" INTEGER,
  "players" TEXT,
  "redTeam" TEXT,
  "blueTeam" TEXT,
  "winner" INTEGER,
  "redCaptain" INTEGER,
  "blueCaptain" INTEGER);""")
        self.close()

