import sqlite3 as sql

def insertUser(username,password):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
    con.commit()
    con.close()

def findtUser(username,password):
	con = sql.connect("database.db")
	cursor = con.cursor()
	cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?',(myusername, mypassword))
	account = cursor.fetchone()
	if account:
		print("found 1")
	else:
		print("not found")
	con.commit()
	con.close()

def retrieveUsers():
	con = sql.connect("database.db")
	cur = con.cursor()
	cur.execute("SELECT username, password FROM users")
	users = cur.fetchall()
	con.close()
	return users

myusername = "vmthanh"
mypassword = "123456789"
findtUser(myusername,mypassword)
