import sqlite3 as lite
import sys
import time

#color testing?
colorTests = True;


#Translation strings (uses {{varible}} and _F(string, [varibles,...]) for adding varibles to strings)
_L = {
        'leftAlert': '!!!!' + ('\t'*14),
        'rightAlert': ('\t'*14)+'!!!!',
        'loading': 'I\'M LOADING UP',
        'userRmGame': 'USER {{1}} REMOVED FROM GAME ID #{{2}}'
    }

#colors for different types of message
_C = {
        'alert': (1, 13),
        'gameMsg': (0, 1),
        'gameError': (4, 1),
        'gameWarning': (8, 1),
        'gameComfirm': (9, 1),
    }

#String Formatter
def _F (string, arg):
    finder = re.compile(r'\{\{([^\}]+)\}\}')
    output = re.sub(finder, lambda i: arg[i.group(1)] if i.group(1) in arg else i.group(0), string)
    return ouput

class channel(object):
    """docstring for channel"""
    def __init__(self, bot):
        super(channel, self).__init__()
        self.bot = bot
        self.userlist = userList()
        self.gamelist = gameList()
        self.db = db()
        self.admins = ['phood', 'klutch']

    def checkUsers(self):
        if colorTests:
            for color in _C:
                textColor, bgColor = _C[color]
                self.bot.sendChannelMsg(_L['leftAlert']+color+_L['rightAlert'], textColor, bgColor)
        else:
            textColor, bgColor = _C['alert']
            self.bot.sendChannelMsg(_L['leftAlert']+_L['loading']+_L['rightAlert'], textColor, bgColor)
        for username in self.bot.nameList:
            self.bot.write('WHOIS', [username])

    def updateUser(self, auth, name):
        if not auth == 'Q':
            usr = self.userlist.findByAuth(auth)
            if not usr:
                usr = User(name)
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

    def userNick(self, usr, msg):
        player = self.userList.findByChannelName(usr)
        if player:
            player.name = msg
            self.db.setUser(player)

    def userOff(self, cmd, usr, msg):
        player = self.userlist.findByChannelName(usr)
        if player:
            for game in self.gamelist.gamelist:
                if player in game:
                    game.remove(player)
                    textColor, bgColor = _C['gameError']
                    self.bot.sendChannelMsg(_F(_L['userRmGame'], [player.name, game.id]))

            self.userlist.remove(player)
            del player


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

class User(object):
    """docstring for User"""
    def __init__(self, name):
        super(User, self).__init__()
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

class gameList(object):
    """docstring for gameList"""
    def __init__(self):
        super(gameList, self).__init__()
        self.gamelist = []

class Game(object):
    """docstring for game"""
    def __init__(self, creator):
        super(game, self).__init__()
        self.creator = creator
        self.idgames = None
        self.status = 0
        self.date = time.time()
        self.players = []
        self.redTeam = []
        self.blueTeam = []
        self.winner = None
        self.redCaptain = None
        self.blueCaptain = None
        
        

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

    def adduser(self, usr):
        sqlinsert = "INSERT INTO users (name, authed, authedAs) VALUES ('"+str(usr.name)+"', "+str(int(usr.authed))+", '"+str(usr.authedAs)+"');"
        self.connect()
        self.cur.execute(sqlinsert)
        self.con.commit()
        rowid = self.cur.lastrowid
        print rowid
        self.close()
        usr.dbID = rowid

    def getUser(self, usr):
        self.connect()
        if usr.dbID:
            self.cur.execute("SELECT count(*) as num, * FROM 'users' WHERE idusers='"+str(usr.dbID)+"' LIMIT 0,1;")
            userexists = self.cur.fetchone()
            if userexists['num']:
                usr.dbID = userexists[1]
        elif usr.authed and usr.authedAs:
            self.cur.execute("SELECT count(*) as num, * FROM 'users' WHERE authedAs='"+str(usr.authedAs)+"' LIMIT 0,1;")
            userexists = self.cur.fetchone()
            if userexists['num'] == 0:
                self.adduser(usr)
            else:
                usr.inGame = userexists['inGame']
                usr.vouchedBy = userexists['vouchedBy']
                usr.dbID = userexists['idusers']
                usr.wotUsername = userexists['wotUsername']
                usr.tanks = userexists['tanks']
                usr.wins = userexists['wins']
                usr.losses = userexists['losses']
                usr.draws = userexists['draws']
                usr.eff = userexists['eff']
                usr.winsix = userexists['winsix']
                usr.winrate = userexists['winrate']
        self.close()

    def setUser(self, usr):
        self.connect()
        if usr.dbID:
            self.cur.execute("UPDATE 'users' SET name='" + str(usr.name) + "', authed='" + str(usr.authed) + "', authedAs='" + str(usr.authedAs) + "', inGame='" + str(usr.inGame) + "', vouchedBy='" + str(usr.vouchedBy) + "', wotUsername='" + str(usr.wotUsername) + "', tanks='" + str(usr.tanks) + "' WHERE idusrs='" + str(usr.dbID)+"'")
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
  "winner" INTEGER,
  "redCaptain" INTEGER,
  "blueCaptain" INTEGER,
  "creator" INTEGER);""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS "game_users" (
  "idgameusers" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "game" INTEGER,
  "date" INTEGER,
  "user" INTEGER);""")
        self.close()

