import sqlite3 as lite
import sys

class channel(object):
    """docstring for channel"""
    def __init__(self, bot):
        super(channel, self).__init__()
        self.bot = bot
        self.userlist = userList()

    def checkUsers(self):
        for username in bot.nameList:
            self.write('WHOIS', [username])

class userList(object):
    """docstring for userList"""
    def __init__(self):
        super(userList, self).__init__()
        self.userList=[]

    def findByChannelName (self, name):
        for player in self.userList:
            if player.name == name:
                return player

    def findByAuth (self, name):
        for player in self.userList:
            if player.auth == name:
                return player

    def findByWotUsername (self, name):
        for player in self.userList:
            if player.wotUsername == name:
                return player

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
            self.cur = self.con.cursor()
        except lite.Error, e:
            print "DATABASE ERROR!"
            sys.exit(1)

    def close(self):
        if self.con:
            self.con.close()

    def adduser(self, user):
        sqlinsert = "INSERT INTO users (name, authed, authedAs, vouchedBy, wotUsername, tanks) VALUES ('"+str(user.name)+"', "+str(int(user.authed))+", '"+str(user.authedAs)+"', "+str(int(user.vouchedBy))+", '"+str(user.wotUsername)+"', '"+str(user.tanks)+"');"
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
            self.cur.execute("SELECT count(*), idusers FROM 'users' WHERE idusers='"+user.dbID+"' LIMIT 0,1;")
            userexists = self.cur.fetchone()
            if userexists[0]:
                user.dbID = userexists[1]
        elif user.authed and user.authedAs:
            self.cur.execute("SELECT count(*), idusers FROM 'users' WHERE authedAs='"+user.authedAs+"' LIMIT 0,1;")
            userexists = self.cur.fetchone()
            self.close()
            if userexists[0] == 0:
                self.adduser(user)
            else:
                user.dbID = userexists[1]

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

        