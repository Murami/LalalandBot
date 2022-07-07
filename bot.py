import interactions

import hashlib
from base64 import b64decode, b64encode

import sqlite3

import asyncio
import logging
import aiohttp
import pyxivapi
from pyxivapi.models import Filter, Sort

import requests
import re
from bs4 import BeautifulSoup

#guild_id=970053878412345374
#potato=970064386662228018
guild_id=868573364762054697
potato=994611463132020846
ephemeral=False
# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
# }

# url = "https://na.finalfantasyxiv.com/lodestone/character/35866243/"

# r = requests.get(url, headers=headers)

# soup = BeautifulSoup(r.content, features="lxml")
# prettyHTML = soup.prettify() 


# raceHTML = soup.select(".character__profile__data__detail .character-block:nth-child(1) .character-block__name")[0]
# race = raceHTML.text.lower()
# isLala = "lalafell" in race



# print(isLala)
# exit(0)

con = sqlite3.connect('lalabot.db')
client = pyxivapi.XIVAPIClient(api_key="37a8188ee522466d9eab22ce37f66214293f180b9ac041fc983db0981d0ecb66")
bot = interactions.Client(token="OTkzODE1NTgwODgyNzYzODI2.G9-4dc.MzseGMR_18RKfqr83Ioa4l9fayf9auDLxxFQtA")

# cur = con.cursor()
# cur.execute("CREATE TABLE user_verification (discord_id, lodestone_id, token, verified)")
# con.commit()

@bot.command(
    name="addpotato",
    description="Add potato rule to user",
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
    scope=guild_id,
    options = [
        interactions.Option(
            name="user",
            description="User",
            type=interactions.OptionType.USER,
            required=True,
        ),
    ]
)
async def addpotato_command(ctx: interactions.CommandContext, user: interactions.Member):
    guild = await ctx.get_guild()
    await user.add_role(guild.id, potato)
    await ctx.send(f"hey {ctx.author.name}, {user.name} has been giving potato role")

@bot.command(
    name="clearlaladb",
    description="Clear the lala registration DB",
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
    scope=guild_id
)
async def clearlaladb_command(ctx: interactions.CommandContext):
    cur = con.cursor()
    cur.execute("DELETE FROM user_verification")
    con.commit()
    await ctx.send("Done.", ephemeral=ephemeral)

@bot.command(
    name="iamlala",
    description="Register yourself as a Lala and get automatically verified.",
    scope=guild_id,
    options = [
        interactions.Option(
            name="world",
            description="World",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="forename",
            description="Forename",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="surname",
            description="Surname",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def iamlala_command(ctx: interactions.CommandContext, world: str, forename: str, surname: str):
    discordId = ctx.user.id

    # Search for character ...
    characterSearchResult = await client.character_search(
        world=world, 
        forename=forename, 
        surname=surname
    )

    if len(characterSearchResult['Results']) == 0:
        await ctx.send("No character found :(")
        return
    elif len(characterSearchResult['Results']) > 1:
        await ctx.send("Too many characters found for this search -_-", ephemeral=ephemeral)
        return
    
    lodesteoneId = characterSearchResult['Results'][0]['ID']

    ## XIVAPI seems to kinda update rly slowly. So for character data we directly scrap lodestone 
    # character = await client.character_by_id(
    #     lodestone_id=lodesteoneId, 
    #     extended=True
    # )
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
    }
    url = "https://na.finalfantasyxiv.com/lodestone/character/{}/".format(lodesteoneId)
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, features="lxml")
    prettyHTML = soup.prettify() 

    ## Parse bio for token
    bioLines = []
    for bio in [ bioHTML.get_text(separator="\n") for bioHTML in soup.select(".character__selfintroduction") ]:
        for line in bio.splitlines():
            bioLines.append(line)

    ## Parse race
    raceHTML = soup.select(".character__profile__data__detail .character-block:nth-child(1) .character-block__name")[0]
    race = raceHTML.text.lower()
    isLala = "lalafell" in race

    # isLala = character['Character']['Race']['ID'] == 3
    # bioLines = character['Character']['Bio'].splitlines()
    # print(bioLines)

    # ... then check if what we already know about it
    cur = con.cursor()
    userVerificationResult = cur.execute("SELECT * FROM user_verification WHERE discord_id=?", (str(discordId), )).fetchall()

    ##################
    ### Not registered / Try to register the user
    print(userVerificationResult)
    if len(userVerificationResult) == 0 or userVerificationResult[0][3] == False:
        
        ## Need to create entry and the token ...
        if len(userVerificationResult) == 0:
            print("no user_verification entry found")
            # token generation
            m = hashlib.md5()
            m.update(str(discordId).encode("utf-8"))
            m.update(str(lodesteoneId).encode("utf-8"))
            authToken = "lalabot-" + str(b64encode(m.digest()))

            # create the entry
            print("create user_verification entry")
            cur.execute("INSERT INTO user_verification VALUES(?, ?, ?, ?)", (str(discordId), str(lodesteoneId), authToken, False))
            con.commit()

            userVerificationResult = cur.execute("SELECT * FROM user_verification WHERE discord_id=?", (str(discordId), )).fetchall()
            entry = userVerificationResult[0]
        ## ... or use the one we got
        else:
            print("1 user_verification entry found")
            entry = userVerificationResult[0]
        
        ## Does the user has the token in its lodestone profile ?
        token = entry[2]
        hasToken = False
        print(bioLines)
        for line in bioLines:
            print(line)
            if line == token:
                hasToken = True

        ## yes, they do so we can register them (if they are lala :p)
        if hasToken:
            if not isLala:
                await ctx.send("No no no ! Only lalas there !", ephemeral=ephemeral)
                return
            else:
                cur.execute("UPDATE user_verification SET verified=? WHERE discord_id=?", (True, str(discordId)))
                con.commit()
                await ctx.send("Congratulations, your account have been verified ! Welcome to Lalaland", ephemeral=ephemeral)
                return

        ## no, we tell them their tokens
        else:
            await ctx.send("Hey, i can't register your character :(\nYou need to put this string into your lodestone bio:\n``{}``".format(token), ephemeral=ephemeral)
            return

    ##################
    ## Registered
    else:
        await ctx.send("Your character is already registered.")
        return
    
bot.start()