import gather

userList = gather.userList()

for i in range(0,15):
	player = gather.user("testuser234234234234-"+str(i))
	player.authed = True
	player.vouchedBy = i-1
	player.authedAs = "testuser-"+str(i)
	player.wotUsername = "testuser24234-"+str(i)
	userList.userList.append(player)


test = gather.db()

for user in userList.userList:
	test.getUser(user)

for user in userList.userList:
	print user.dbID