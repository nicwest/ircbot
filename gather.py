import sqlite3 as lite
import sys
import time
import re

#color testing?
colorTests = False;



#Translation strings (uses {{varible}} and _F(string, [varibles,...]) for adding varibles to strings)
_L = {
        'leftAlert': '!!!!' + ('\t'*14),
        'rightAlert': ('\t'*14)+'!!!!',
        'loading': 'I\'M LOADING UP',
        'userRmGame': 'USER {{0}} REMOVED FROM GAME ID #{{1}}',
        'gameForming': 'GAME ID #{{0}} FORMING BY {{1}}',
        'gameStillForming': 'A GAME IS CURRENTLY FORMING, PLEASE JOIN THAT ONE OR WAIT FOR IT TO START BEFORE FORMING A NEW GAME',
        'gameFormingStatus': 'GAME ID #{{0}} {{1}}/{{2}} PLAYERS, TYPE !JOIN TO PLAY',
        'noGame': 'NO GAME CURRENTLY FORMING. TYPE !START TO START ONE',
        'gameFull': 'GAME IS FULL, PLEASE WAIT FOR CURRENT GAME TO FINISH FORMING BEFORE STARTING A NEW ONE WITH !START',
        'alreadyInGame': 'YOU ARE ALREADY IN A GAME YOU DICKBAG!',
    }

#colors for different types of message
_C = {
        'alert': (1, 13),
        'gameMsg': (0, 1),
        'gameError': (4, 1),
        'gameWarning': (8, 1),
        'gameComfirm': (9, 1),
        'channelMsg': (0, 2),
        'channelError': (4, 2),
        'channelWarning': (8, 2),
        'channelComfirm': (9, 2),
    }

#String Formatter
def _F (string, arg):
    finder = re.compile(r'\{\{([^\}]+)\}\}')
    output = re.sub(finder, lambda i: str(arg[int(i.group(1))]) if arg[int(i.group(1))] else i.group(0), string)
    #output = re.sub(finder, lambda i: 'foo, string)

    return output

class channel(object):
    """docstring for channel"""
    def __init__(self, bot):
        super(channel, self).__init__()
        self.bot = bot
        self.userlist = userList()
        self.gamelist = gameList()
        self.db = db()
        self.admins = ['phood', 'KLUTCH-']

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
                usr.vouchedBy = "server"
                self.bot.write('PRIVMSG', ['Q'], 'CHANLEV ' + self.bot.channel + ' ' + usr.name + ' ' + '+o')
            elif usr.vouchedBy:
                self.bot.write('PRIVMSG', ['Q'],  'CHANLEV ' + self.bot.channel + ' ' + usr.name + ' ' + '+v')

    def takeCommand(self, usr, msg):
        if msg.find(' ') > 0:
            action, cmd = msg.split(' ', 1)
        else:
            action, cmd = (msg, '')
        usr = self.userlist.findByChannelName(usr)
        action = action.lower()
        if usr and usr.vouchedBy:
            if action == "!vouch" and len(cmd) > 0:
                for usrname in cmd.split(' '):
                    vouchee = self.userlist.findByChannelName(usrname)
                    if vouchee:
                        self.vouch(usr, vouchee)
            if action == "!start":
                self.startGame(usr)
            if action == "!join":
                self.joinGame(usr)

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

    def gameStatus(self, game):
        if game:
            currentPlayers = len(game.players)
            if currentPlayers < game.teamsize:
                textColor, bgColor = _C['gameMsg']
                self.bot.sendChannelMsg(_F(_L['leftAlert']+_L['gameFormingStatus']+_L['rightAlert'], [game.dbID, currentPlayers, game.teamsize]), textColor, bgColor)
            else:
                self.pickingStart(game)

    def pickingStart(self, game):
        pass

    def startGame(self, player):
        if player.status == 0:
            if not self.gamelist.forming:
                newgame = Game(player)
                self.db.addGame(newgame)
                self.gamelist.forming = newgame

                textColor, bgColor = _C['gameMsg']
                self.bot.sendChannelMsg(_F(_L['leftAlert']+_L['gameForming']+_L['rightAlert'], [newgame.dbID, player.name]), textColor, bgColor)

                self.joinGame(player)
            else:
                textColor, bgColor = _C['channelWarning']
                self.bot.sendChannelNotice(player.name, _L['leftAlert']+_L['gameStillForming']+_L['rightAlert'], textColor, bgColor)
        else:
            textColor, bgColor = _C['gameWarning']
            self.bot.sendChannelNotice(player.name, _L['leftAlert']+_L['alreadyInGame']+_L['rightAlert'], textColor, bgColor)
            

    def joinGame(self, player):
        if self.gamelist.forming:
            game = self.gamelist.forming
            if len(game.players) < game.teamsize:
                if player not in game.players and player.status == 0:
                    player.status = 1
                    game.players.append(player)
                    self.db.setUser(player)
                    self.db.addPlayerToGame(player, game)
                    self.db.updatePlayerGameStatus(game, player, 1)
                    self.gameStatus(game)
                else:
                    textColor, bgColor = _C['gameWarning']
                    self.bot.sendChannelNotice(player.name, _L['leftAlert']+_L['alreadyInGame']+_L['rightAlert'], textColor, bgColor)
            else:
                textColor, bgColor = _C['gameWarning']
                self.bot.sendChannelNotice(player.name, _L['leftAlert']+_L['gameFull']+_L['rightAlert'], textColor, bgColor)
        else:
            textColor, bgColor = _C['channelMsg']
            self.bot.sendChannelMsg(_L['leftAlert']+_L['noGame']+_L['rightAlert'], textColor, bgColor)


    def leaveGame(self, player):
        if player:
            for game in self.gamelist.gamelist:
                if player in game.players:
                    if player in game.blueTeam:
                        game.blueTeam.remove(player)
                    if player in game.redTeam:
                        game.redTeam.remove(player)
                    game.remove(player)
                    player.status = 0

                    self.db.setUser(player)
                    self.db.updatePlayerGameStatus(game, player, 0)

                    textColor, bgColor = _C['gameError']
                    self.bot.sendChannelMsg(_F(_L['leftAlert']+_L['userRmGame']+_L['rightAlert'], [player.name, game.id]), textColor, bgColor)
                    self.gameStatus(game)

    def userOff(self, cmd, usr, msg):
        player = self.userlist.findByChannelName(usr)
        if player:
            self.leaveGame(player)
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
        self.status = 0
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
        self.forming = None

class Game(object):
    """docstring for game"""
    def __init__(self, creator):
        super(Game, self).__init__()
        self.creator = creator
        self.dbID = None
        self.status = 0
        self.date = time.time()
        self.players = []
        self.redTeam = []
        self.blueTeam = []
        self.winner = None
        self.redCaptain = None
        self.blueCaptain = None 
        self.teamsize = 14       
        

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

    def addGame(self, game):
        sqlinsert = "INSERT INTO games (status, date, winner, redCaptain, blueCaptain, creator) VALUES ('"+str(game.status)+"', '"+str(game.date)+"', '"+str(game.winner)+"', '"+str(game.redCaptain)+"', '"+str(game.blueCaptain)+"', '"+str(game.creator)+"');"
        self.connect()
        self.cur.execute(sqlinsert)
        self.con.commit()
        rowid = self.cur.lastrowid
        print rowid
        self.close()
        game.dbID = rowid

    def getGame(self, game):
        self.connect()
        if game.dbID:
            self.cur.execute("SELECT count(*) as num, * FROM 'games' WHERE idgames='"+str(game.dbID)+"' LIMIT 0,1;")
            gameexists = self.cur.fetchone()
            if gameexists['num']:
                usr.creator = gameexists['inGame']
                usr.dbID = gameexists['vouchedBy']
                usr.status = gameexists['idusers']
                usr.date = gameexists['wotUsername']
                usr.players = gameexists['tanks']
                usr.redTeam = gameexists['wins']
                usr.blueTeam = gameexists['losses']
                usr.winner = gameexists['draws']
                usr.redCaptain = gameexists['eff']
                usr.blueCaptain = gameexists['winsix']
        self.close()

    def setGame(self, game):
        self.connect()
        if game.dbID:
            self.cur.execute("UPDATE 'games' SET status='" + str(game.status) + "', date='" + str(game.date) + "', winner='" + str(game.winner) + "', redCaptain='" + str(game.redCaptain) + "', blueCaptain='" + str(game.blueCaptain) + "', creator='" + str(game.creator) + "' WHERE idgames='" + str(game.dbID)+"'")
            self.con.commit()
        self.close()

    def adduser(self, usr):
        sqlinsert = "INSERT INTO users (name, authed, authedAs, status) VALUES ('"+str(usr.name)+"', "+str(int(usr.authed))+", '"+str(usr.authedAs)+"', '"+str(usr.status)+"');"
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
                usr.status = userexists['status']
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
        elif usr.authed and usr.authedAs:
            self.cur.execute("SELECT count(*) as num, * FROM 'users' WHERE authedAs='"+str(usr.authedAs)+"' LIMIT 0,1;")
            userexists = self.cur.fetchone()
            if userexists['num'] == 0:
                self.adduser(usr)
            else:
                usr.status = userexists['status']
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
            self.cur.execute("UPDATE 'users' SET name='" + str(usr.name) + "', authed='" + str(usr.authed) + "', authedAs='" + str(usr.authedAs) + "', status='" + str(usr.status) + "', vouchedBy='" + str(usr.vouchedBy) + "', wotUsername='" + str(usr.wotUsername) + "', tanks='" + str(usr.tanks) + "' WHERE idusers='" + str(usr.dbID)+"'")
            self.con.commit()
        self.close()

    def addPlayerToGame(self, player, game):
        self.connect()
        if game.dbID and player.dbID:
            self.cur.execute("INSERT INTO game_users (game, date, user, status) VALUES ('" + str(game.dbID) + "','" + str(time.time()) + "','" + str(player.dbID) + "','0')")
            self.con.commit()
        self.close()

    def updatePlayerGameStatus(self, game, player, status):
        self.connect()
        if game.dbID and player.dbID:
            self.cur.execute("UPDATE 'game_users' SET status='"+str(status)+"' WHERE game='"+str(game.dbID)+"' AND user='"+str(player.dbID)+"'")
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
  "status" INTEGER DEFAULT 0,
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
  "user" INTEGER,
  "status" INTEGER);""")
        self.close()

