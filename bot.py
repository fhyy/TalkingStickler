import discord
import os
import re
import ids
from datetime import datetime
from pytz import timezone

class RollsLevel:
    highestRoll = 0
    rolls = []
    nextRollsLevel = None

    def __init__(self,id,roll):
        self.rolls.append((id, roll))
        self.highestRoll = roll
    
    def addRoll(self,id, roll):
        prevRoll = self.getRoll(id)
        if prevRoll == None:
            self.rolls.append((id, roll))
            if roll == self.highestRoll:
                self.nextRollsLevel = RollsLevel(id, roll)
            elif roll > self.highestRoll:
                if self.nextRollsLevel != None:
                    self.nextRollsLevel.clear()
            return True
        if prevRoll == self.highestRoll and self.nextRollsLevel != None:
            return self.nextRollsLevel.addRoll(id, roll)
        else:
            return False
    
    def clear(self,):
        if self.nextRollsLevel != None:
            self.nextRollsLevel.clear()
            self.nextRollsLevel = None
        
    def getRoll(self,id):
        for rollId, roll in self.rolls:
            if id == roleId:
                return roll
        return None
        
    def hasHighestRoll(self,id):
        if id == self.getHighestRoll():
            return True
        return False
        
    def getHighestRoll(self):
        for rollId, roll in self.rolls:
            if roll == self.highestRoll:
                if self.nextRollsLevel != None:
                    return self.nextRollsLevel.getHighestRoll()
            return rollId
        return None # Should not be the case
        
    def getTies(self):
        ties = []
        for rollId, roll in self.rolls:
            if roll == self.highestRoll:
                ties.append(rollId)
        if self.nextRollsLevel != None:
            ties = ties + self.nextRollsLevel.getTies()
        ties.remove(self.getHighestRoll())
        return list(set(ties))
        
intents = discord.Intents(messages=True, members=True, guilds=True)
client = discord.Client(intents=intents)

tz = timezone('Europe/Stockholm')

diceBotId = ids.diceBotId
channelId = ids.channelId
roleId = ids.roleId
clientKey = ids.clientKey

lastRollDate = tz.utcoffset(datetime.utcnow()) + datetime.utcnow()
rollsLevel = None

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global rollsLevel
    global highestRoll
    global tz
    global diceBotId
    global channelId
    global roleId

    if message.author == client.user or message.channel.id != channelId:
        return

    date = message.created_at
    date = tz.utcoffset(date) + date;

    if message.content == "Stickler what time is it?":
        await client.get_channel(channelId).send("It's "+str(date))

    if message.author.id == diceBotId:
        nums = re.findall(r'\d+', message.content) #"<@123456> You rolled 15"
        if len(nums) < 2:
            return

        id = int(nums[0])
        roll = int(nums[1])

        updateDate(date)

        if rollsLevel == None:
            rollsLevel = RollsLevel(id, roll)
        else:
            if rollsLevel.addRoll(id, roll):
                if rollsLevel.hasHighestRoll(id):
                    await assignStick(message, id)
                else:
                    ties = rollsLevel.getTies()
                    if id in ties:
                        await notifyTieBreaker(message, ties)
            else:
                await client.get_channel(channelId).send("Don't you go cheating now <@"+str(id)+">")

async def assignStick(message, id):
    global channelId
    global roleId
    await client.get_channel(channelId).send("<@"+str(id)+">, you've got the stick now!")
    await clearRole(extractMembers(message), message.guild.get_role(roleId))
    await setRole(message.guild.get_member(id), message.guild.get_role(roleId))

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

def get_member_id_with_nickname(nick, members):
    for member in members:
        if member.nickname == nick:
            return member.id
    return -1

def get_member_id_with_nickname(name, members):
    for member in members:
        if member.name == name:
            return member.id
    return -1

def get_all_members_ids(guild):
    for member in guild.members:
        yield member.id

client.run(clientKey)