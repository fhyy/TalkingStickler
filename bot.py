import discord
import os
import re
import ids
import random
import asyncio
from datetime import datetime
from datetime import timedelta
from pytz import timezone

class RollsLevel:
    def __init__(self):
        self.highestRoll = 0
        self.rolls = []
        self.nextRollsLevel = None
    
    def addRoll(self, id, roll):
        prevRoll = self.getRoll(id)
        if prevRoll == None:
            self.rolls.append({"id": id, "roll": roll})
            if roll == self.highestRoll:
                if self.nextRollsLevel == None:
                    self.nextRollsLevel = RollsLevel()
            if roll > self.highestRoll:
                self.highestRoll = roll
                self.tied = False
                if self.nextRollsLevel != None:
                    self.nextRollsLevel.clear()
                    self.nextRollsLevel = None
            return True
        if prevRoll == self.highestRoll:
            if self.nextRollsLevel == None:
                return False
            return self.nextRollsLevel.addRoll(id, roll)
        else:
            return False
    
    def clear(self):
        if self.nextRollsLevel != None:
            self.nextRollsLevel.clear()
            self.nextRollsLevel = None
        
    def getRoll(self,id):
        for roll in self.rolls:
            if id == roll["id"]:
                return roll["roll"]
        return None
        
    def hasHighestRoll(self,id):
        if id == self.getHighestRoll()["id"]:
            return True
        return False
        
    def getHighestRoll(self):
        for roll in self.rolls:
            if roll["roll"] == self.highestRoll:
                if self.nextRollsLevel != None:
                    return self.nextRollsLevel.getHighestRoll()
                return roll
        return {"id": '0', "roll": 0}
        
    def getTies(self):
        ties = []
        if self.nextRollsLevel != None:
            for roll in self.rolls:
                if roll["roll"] == self.highestRoll:
                    if self.nextRollsLevel.getRoll(roll["id"]) == None:
                        ties.append(roll["id"])
            ties = ties + self.nextRollsLevel.getTies()
        return list(set(ties))
        
intents = discord.Intents(messages=True, members=True, guilds=True)
client = discord.Client(intents=intents)

tz = timezone('Europe/Stockholm')

diceBotId = ids.diceBotId
channelId = ids.channelId
musicChannelId = ids.musicChannelId
roleId = ids.roleId
clientKey = ids.clientKey
currentDeathRoll = 1000

lastRollDate = tz.utcoffset(datetime.utcnow()) + datetime.utcnow()
rollsLevel = None

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global tz
    global channelId
    global currentDeathRoll

    if message.author == client.user or message.channel.id != channelId:
        return
    date = message.created_at
    date = tz.utcoffset(date) + date;
    
    if message.content == "Stickler what time is it?":
        await client.get_channel(channelId).send("It's "+str(date))
        
    if message.content.startswith('!h'):
        await sendMessage('`!rfs` roll for stick (d20)\n'
                          '`!roll d<sides>` or `!roll d<sides> <num>` for rolling dice\n'
                          '`!dr` or `!dr restart` for death roll or restarting')
    if message.content.startswith('!rfs'):
        roll = rollDice(20)
        await sendMessage("<@"+str(message.author.id)+"> rolled " + str(roll))
        await talkingStick(message, roll, date)
    #if message.content.startswith('!static'):
    #    matches = re.search('!static (\d+)', message.content)
    #    if matches == None or matches.group(1) == None:
    #        return
    #    roll = int(matches.group(1))
    #    await sendMessage("<@"+str(message.author.id)+"> rolled " + str(roll))
    if message.content.startswith('!roll'):
        matches = re.search('!roll d(\d+)( (\d+))?', message.content)
        if matches == None or matches.group(1) == None:
            return
        sides = int(matches.group(1))
        number = 1
        if matches.group(3) != None:
            number = int(matches.group(3))
        if sides < 9999:
            if number == 1:
                roll = rollDice(sides)
                await sendMessage("<@"+str(message.author.id)+"> rolled " + str(roll))
            elif number < 999:
                results = rollMultipleDice(sides, number)
                rollsString = ""
                rolls = results["rolls"]
                total = results["total"]
                for i in range(0,len(rolls)):
                    if i == len(rolls):
                        rollsString = rollsString + str(rolls[i])
                    else:
                        rollsString = rollsString + str(rolls[i]) + ", "
                        
                await sendMessage("<@"+str(message.author.id)+"> rolled " + rollsString+ " = " + str(total) + " (total)")
            
    if message.content.startswith('!dr'):
        if message.content.startswith('!dr restart'):
            currentDeathRoll = 1000
            await sendMessage("Death roll starting over!")
        else:
            roll = rollDice(currentDeathRoll)
            fromNum = currentDeathRoll
            if roll == 1:
                currentDeathRoll = 1000
                await sendMessage("<@"+str(message.author.id)+"> rolled " + str(roll) + "/" + str(fromNum) + " and lost!")
                await sendMessage("Death roll starting over!")
            else:
                currentDeathRoll = roll
                await sendMessage("<@"+str(message.author.id)+"> rolled " + str(roll) + "/" + str(fromNum))
            
async def talkingStick(message, roll, date):
    global rollsLevel
    global highestRoll
    global channelId
    global roleId
    id = message.author.id
    updateDate(date)

    if rollsLevel == None:
        rollsLevel = RollsLevel()

    if rollsLevel.addRoll(id, roll):
        if rollsLevel.hasHighestRoll(id):
            await assignStick(message, id)
        else:
            ties = rollsLevel.getTies()
            if id in ties:
                await notifyTieBreaker(message, ties)
    else:
        await client.get_channel(channelId).send("<@"+str(id)+"> don't you go cheating now!")

async def assignStick(message, id):
    global channelId
    global roleId
    await sendMessage("<@"+str(id)+">, you've got the stick now!")
    await clearRole(extractMembers(message), message.guild.get_role(roleId))
    await setRole(message.guild.get_member(id), message.guild.get_role(roleId))

async def sendMessage(message):
    await client.get_channel(channelId).send(message)
    
async def notifyTieBreaker(message, ties):
    text = "Remember to roll your tie breaker rolls!"
    for id in ties:
        text = text + "\n<@"+str(id)+">"
    await client.get_channel(channelId).send(text)
    
async def clearRole(members, role):
    for member in members:
        if role in member.roles:
            await member.remove_roles(role)

async def setRole(member, role):
    await member.add_roles(role)

def rollMultipleDice(sides, num):
    rolls = []
    total = 0
    for i in range(0,num):
        roll = rollDice(sides)
        rolls.append(roll)
        total = total + roll
    return {"rolls":rolls,"total":total}
    
def rollDice(sides):
    return random.randint(1,sides)
    
def isCheating(id, roll):
    global rollsToday
    for rolls in rollsToday:
        if rolls["id"] == id:
            return True
    return False

def updateDate(date):
    global lastRollDate
    global rollsLevel
    if lastRollDate.date() < date.date():
       rollsLevel.clear()
       rollsLevel = None
    lastRollDate = date

def isIdInMembers(members, id):
    for member in members:
        if member.id == id:
            return True
    return False

def extractMembers(message):
    return message.guild.members

async def midnightJob():
    await client.get_channel(musicChannelId).send("-p feeling good")

lastDay = 0

def secondsUntilEndOfToday():
    dateNow = datetime.now()
    dateNow = tz.utcoffset(dateNow) + dateNow;
    dTime = datetime.combine(
        dateNow.date() + timedelta(days=1), datetime.strptime("0000", "%H%M").time()
    ) - dateNow
    return dTime.seconds

def checkIfNewDay():
    global lastDay
    date = datetime.now()
    date = tz.utcoffset(date) + date;
    return lastDay != date.day

async def checkIfAndRunMidnightTask():
    if checkIfNewDay():
        await midnightJob()

async def scheduledTasks():
    global lastDay
    lastDay = date.day
    while True:
        timeUntilMidnightSeconds = secondsUntilEndOfToday()
        await asyncio.sleep(min(timeUntilMidnightSeconds, 10))
        await checkIfAndRunMidnightTask()
        date = datetime.now()
        date = tz.utcoffset(date) + date;
        lastDay = date.day

asyncio.get_event_loop().create_task(scheduledTasks())
client.run(clientKey)
