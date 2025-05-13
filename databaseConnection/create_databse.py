# importing required libraries

import mysql.connector

dataBase = mysql.connector.connect(

host ="localhost",

user ="root",

passwd ="AellaSushma@2002"

)

print(dataBase)

cursorObj= dataBase.cursor()
cursorObj.execute("CREATE DATABASE pydb")#create database

# Disconnecting from the server

dataBase.close()