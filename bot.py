import discord
import os
import re
import ids
from datetime import datetime
from pytz import timezone

intents = discord.Intents(messages=True, members=True, guilds=True)
client = discord.Client(intents=intents)

tz = timezone('Europe/Stockholm')

diceBotId = ids.diceBotId
channelId = ids.channelId
roleId = ids.roleId
clientKey = ids.clientKey

lastRollDate = tz.utcoffset(datetime.utcnow()) + datetime.utcnow()
rollsToday = []
highestRoll = 0

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global rollsToday
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

        if isCheating(id, roll):
            await client.get_channel(channelId).send("Don't you go cheating now <@"+str(id)+">")
        else:
            rollsToday.append({"id":id,"roll":roll})
            if roll > highestRoll:
                highestRoll = roll
                await client.get_channel(channelId).send("<@"+str(id)+">, you've got the stick now!")
                await clearRole(extractMembers(message), message.guild.get_role(roleId))
                if roll == highestRoll:
                    await setRole(message.guild.get_member(id), message.guild.get_role(roleId))

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
    global rollsToday
    global highestRoll
    if lastRollDate.date() < date.date():
       rollsToday.clear()
       highestRoll = 0
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