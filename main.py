import asyncio
import config
import discord
import logging
import uvloop
from bot import Bot
from functools import wraps
from models import *

party = "🎉"

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

client = discord.Client()

bot = Bot(client)

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d: %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger

logger = get_logger('taso')

async def mxp(level):
    return (45 + (5 * level))

async def diff(level):
    return max(0, (5 * (level - 30)))

async def levelup(level, exp):
    req = ((8 * level) + await diff(level)) * await mxp(level)
    newexp = exp + await mxp(level)

    if newexp >= req:
        newexp = newexp - req
        newlvl = level + 1

        return newlvl, newexp

    return level, newexp

lock = asyncio.Lock()

async def reply(text, message):
    m = await client.send_message(
        message.channel,
        text
    )
    await asyncio.sleep(10)

    await client.delete_message(m)
    await client.delete_message(message)

@bot.command('announce_channel', discord.Permissions(32))
async def announce_channel(message):
    server = Server.get(Server.sid == message.server.id)
    server.announce_channel = message.channel.id
    await reply(f"I will now do server level up announcements here.", message)

@bot.command('iam')
async def add_role(message):
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = discord.utils.get(message.server.roles, name=rolename)
    try:
        r = Role.get(Role.rid == role.id)
        if r.assignable:
            await client.add_roles(message.author, role)
    except DoesNotExist as e:
        return

    await reply(f"I have given you the {rolename} role", message)

@bot.command('iamnot')
async def remove_role(message):
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = discord.utils.get(message.server.roles, name=rolename)
    try:
        r = Role.get(Role.rid == role.id)
        if r.assignable:
            await client.remove_roles(message.author, role)
    except DoesNotExist as e:
        return

    await reply(f"I have removed the {rolename} role from you", message)

@bot.command('addrole', discord.Permissions(32))
async def add_role(message):
    # Adds an assignable role
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = discord.utils.get(message.server.roles, name=rolename)
    server = Server.get(Server.sid == message.server.id)
    r, created = Role.get_or_create(
        rid=role.id,
        defaults={
            'assignable': True,
            'server': server
        }
    )
    if not created:
        r.assignable = True
        r.save()

    await reply(f"The {rolename} role is now assignable", message)

@bot.command('removerole', discord.Permissions(32))
async def remove_role(message):
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = discord.utils.get(message.server.roles, name=rolename)
    try:
        r = Role.get(Role.rid == role.id)
        r.assignable = False
        r.save()
    except DoesNotExist as e:
        return

    await reply(f"The {rolename} role is now assignable", message)

@bot.command('addreward', discord.Permissions(32))
async def add_reward(message):
    # Adds an reward role
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:-1])
    level = splitmsg[-1]
    role = discord.utils.get(message.server.roles, name=rolename)
    server = Server.get(Server.sid == message.server.id)
    r, created = Role.get_or_create(
        rid=role.id,
        defaults={
            'awardlevel': level,
            'server': server
        }
    )
    if not created:
        r.awardlevel = level
        r.save()

    await reply(
        f"The {rolename} role will now be given when a user hits level {level}",
        message
    )

@bot.command('removereward', discord.Permissions(32))
async def remove_reward(message):
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = discord.utils.get(message.server.roles, name=rolename)
    try:
        r = Role.get(Role.rid == role.id)
        r.awardlevel = None
        r.save()
    except DoesNotExist as e:
        return

    await reply(
        f"The {rolename} role will no longer given as a levelling reward",
        message
    )

@client.event
async def on_ready():
    print(f"{client.user.name} ({client.user.id}) is now online!")

@client.event
async def on_message(message):
    lmsg = None
    smsg = None
    async with lock:
        if not message.author.bot:
            server, created = Server.get_or_create(
                    sid=message.server.id)
            user, created = User.get_or_create(
                    uid=message.author.id)
            local, created = LocalLevel.get_or_create(
                    user=user,
                    server=server)

            if message.content.startswith('taso.'):
                fields = message.content.split()
                cmd = fields[0].split('.')[1]
                await bot.call(cmd, message)

            level, exp = await levelup(
                    server.level,
                    server.experience)
            try:
                if level > server.level:
                    # Yay, the server leveled up
                    if server.announce_channel:
                        channel = client.get_channel(
                                f'{server.announce_channel}')
                        smsg = await client.send_message(channel,
                                f"{party} {message.server.name} is now level {level}! {party}")
            except Exception as e:
                pass

            server.level = level
            server.experience = exp
            server.save()

            level, exp = await levelup(
                    user.level,
                    user.experience)

            user.level = level
            user.experience = exp
            user.save()

            level, exp = await levelup(
                    local.level,
                    local.experience)
            try:
                if level > local.level:
                    # User leveled up on the server
                    lmsg = await client.send_message(message.channel,
                            f"{party} {message.author.name}, you have leveled up to level {level} on {message.server.name}!! {party}")
                    try:
                        role = Role.get(Role.awardlevel == level)
                        lastrole = Role.select().where(
                            Role.server == server and Role.awardlevel.is_null(False)).order_by(
                                Role.awardlevel.desc()
                            ).limit(1)
                        if len(lastrole) > 0:
                            r = discord.utils.get(message.server.roles, id=f'{lastrole[0].rid}')
                            try:
                                await client.remove_roles(message.author, r)
                            except BaseException as e:
                                pass
                        r = discord.utils.get(message.server.roles, id=f'{role.rid}')
                        await client.add_roles(message.author, r)
                    except DoesNotExist as e:
                        logger.exception("Could not find level up reward")
            except Exception as e:
                logger.exception("Could not process level up")



            local.level = level
            local.experience = exp
            local.save()

    await asyncio.sleep(10)
    if lmsg:
        await client.delete_message(lmsg)
    if smsg:
        await client.delete_message(smsg)

cfg = config.botConfig()
client.run(cfg.token)
