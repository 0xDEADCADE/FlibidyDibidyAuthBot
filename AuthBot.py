# FlibidyDibidy Discord authentication bot
# Written by 0xDEADCADE

# Builtins
import os
import random
import json
import hashlib
import requests

# External dependencies
import discord

# Check for and open settings
if os.path.exists("./Settings.json"):
    with open("./Settings.json", "r") as f:
        Settings = json.load(f)
else:
    print("Please create and fill the Settings.json file.")
    exit()

# Preset variables to None for later use
# Is used to remove reactions
ReactMessage = None
ReactChannel = None

class MyClient(discord.Client):

    async def on_ready(self):
        global Settings, ReactMessage, ReactChannel
        print("Logged in as", str(client.user))
        await client.change_presence(activity=discord.Game(name="FlibidyDibidy Auth Bot"))
        if Settings["MessageID"] is not None:
            ReactChannel = await client.fetch_channel(Settings["ChannelID"])
            ReactMessage = await ReactChannel.fetch_message(Settings["MessageID"])

    async def on_message(self, message):
        # We require global definition here because of async functions
        global Settings, ReactMessage, ReactChannel
        # We do not want to check bots
        if message.author.bot:
            return
        # If the message author is the bot owner
        if message.author.id == Settings["OwnerID"]:
            SplitMessage = message.content.split(" ")
            # If the first part of the message is !sendmessage
            if SplitMessage[0].lower() == "!sendmessage":
                # Repeat what was sent, without !sendmessage
                message = await message.channel.send(" ".join(SplitMessage[1:]))
                # React to the message with thumbs_up
                await message.add_reaction("👍")
                # Update message we're using to remove reactions from
                ReactMessage = message
                # Open and update settings
                Settings["ChannelID"] = message.channel.id
                Settings["MessageID"] = message.id
                with open("./Settings.json", "w") as f:
                    json.dump(Settings, f, indent=4)

    async def on_raw_reaction_add(self, payload):
        global Settings, ReactMessage, ReactChannel
        # If we're seeing our own reaction come in
        if payload.user_id == client.user.id:
            return
        # If the reaction is in the right channel
        if payload.channel_id == Settings["ChannelID"]:
            # And the message is the correct one
            if payload.message_id == Settings["MessageID"]:
                # And it's the right reaction
                if str(payload.emoji) == "👍":
                    # Remove the reaction
                    await ReactMessage.remove_reaction("👍", payload.member)
                    # Check if the user already has the role
                    for role in payload.member.roles:
                        if role.id == Settings["RoleID"]:
                            return
                    # Generate 2 tokens, one single use and one permanent
                    Tokens = [hashlib.sha1(bytes(str(random.random() * random.randint(0,1000)), "utf-8")).hexdigest() for _ in range(2)]
                    try:
                        # Try to send a message as DM to the user who reacted
                        await payload.member.send("Please use this link to log in with your Discord account:\nhttps://flibidydibidy.com/login?token=" + Tokens[0])
                    except Exception as e:
                        # If it failed, notify the user to turn on DMs from server members
                        await ReactChannel.send(f"{payload.member.mention} Please enable messages from server members.\nServer Settings>Privacy Settings>Allow direct messages from server members", delete_after=30)
                        return
                    await payload.member.add_roles(discord.Object(Settings["RoleID"]))
                    Data = json.dumps({"Tokens": Tokens, "UserID": payload.user_id, "UserName": str(payload.member), "ProfilePicture": str(payload.member.avatar_url)})
                    print(Data)


client = MyClient()
client.run(Settings["Token"])
