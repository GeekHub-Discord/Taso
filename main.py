import asyncio
import concurrent.futures
import config
import discord
import logging
import uvloop
from bot import Bot
from models import Server, User, LocalLevel, Role

party = "🎉"

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

client = discord.Client()
pool = concurrent.futures.ThreadPoolExecutor()
client.loop.set_default_executor(pool)


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


def _removeNonAscii(s): return "".join(i for i in s if ord(i) < 128)


@bot.command('announce_channel', discord.Permissions(32))
async def announce_channel(message):
    server = Server.get(Server.sid == message.server.id)
    server.announce_channel = message.channel.id
    await reply(f"I will now do server level up announcements here.", message)


@bot.command('iam')
async def iam(message):
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = None
    for ro in message.server.roles:
        if ro.name.lower() == rolename.lower():
            role = ro
    try:
        r = Role.get(Role.rid == role.id)
        if r.assignable:
            await client.add_roles(message.author, role)
    except Role.DoesNotExist as e:
        return

    await reply(f"I have given you the {rolename} role", message)


@bot.command('iamnot')
async def iamnot(message):
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = None
    for ro in message.server.roles:
        if ro.name.lower() == rolename.lower():
            role = ro
    try:
        r = Role.get(Role.rid == role.id)
        if r.assignable:
            await client.remove_roles(message.author, role)
    except Role.DoesNotExist as e:
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
    except Role.DoesNotExist as e:
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
        f"The {rolename} role will now be given when a user"
        f" hits level {level}",
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
    except Role.DoesNotExist as e:
        return

    await reply(
        f"The {rolename} role will no longer given as a levelling reward",
        message
    )


@bot.command('addleaderrole', discord.Permissions(32))
async def add_leader_role(message):
    # Adds a leaderboard role
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = discord.utils.get(message.server.roles, name=rolename)
    server = Server.get(Server.sid == message.server.id)
    r, created = Role.get_or_create(
        rid=role.id,
        defaults={
            'awardlevel': None,
            'leaderboard': True,
            'server': server
        }
    )
    if not created:
        r.leaderboard = True
        r.save()

    await reply(
        f"The {rolename} role will now be given when a user enters"
        " the leaderboard",
        message
    )


@bot.command('removeleaderrole', discord.Permissions(32))
async def remove_leader_role(message):
    splitmsg = message.content.split()
    rolename = ' '.join(splitmsg[1:])
    role = discord.utils.get(message.server.roles, name=rolename)
    try:
        r = Role.get(Role.rid == role.id)
        r.leaderboard = False
        r.save()
    except Role.DoesNotExist as e:
        return

    await reply(
        f"The {rolename} role will no longer given as a leaderboard reward",
        message
    )


@bot.command("profile")
async def profile(message):
    server = Server.get(Server.sid == message.server.id)
    user = User.get(User.uid == message.author.id)
    lvl = LocalLevel.get(
        (LocalLevel.user == user) &
        (LocalLevel.server == server)
    )
    req = ((8 * lvl.level) + await diff(lvl.level)) * await mxp(lvl.level)
    experience = f"{lvl.experience}/{req}"
    lines = [
        f"{'Level'.ljust(8)}{'Experience'.ljust(10)}",
        f"{str(lvl.level).ljust(8)}{experience.ljust(10)}"
    ]

    msg = '\n'.join(lines)

    await client.send_message(message.channel, f"```{msg}```")


@bot.command("leaderboard")
async def leaderboard(message):
    server = Server.get(Server.sid == message.server.id)
    leaders = LocalLevel.select().where(
        LocalLevel.server == server
    ).order_by(
        LocalLevel.level.desc(), LocalLevel.experience.desc()
    ).limit(10)

    lines = []
    lines.append(
        f"{'Username'.ljust(32)}{'Level'.ljust(8)}{'XP'.ljust(10)}"
    )
    for l in leaders:
        m = message.server.get_member(f"{l.user.uid}")
        req = ((8 * l.level) + await diff(l.level)) * await mxp(l.level)
        expstr = f"{l.experience}/{req}"
        if m is not None:
            username = _removeNonAscii(m.name)
        else:
            username = "Unknown User"
        lines.append(
            f"{username.ljust(32)}{str(l.level).ljust(8)}{expstr.ljust(10)}"
        )

    msg = '\n'.join(lines)

    codeblock = f"```{msg}```"
    await client.send_message(message.channel, codeblock)


@client.event
async def on_ready():
    logger.info(f"{client.user.name} ({client.user.id}) is now online!")


@client.event
async def on_message(message):
    lmsg = None
    smsg = None
    if not message.author.bot:
        if message.content.startswith('taso.'):
            fields = message.content.split()
            cmd = fields[0].split('.')[1]
            await bot.call(cmd, message)
            return
    async with lock:
        if not message.author.bot:
            server, created = Server.get_or_create(
                    sid=message.server.id)
            user, created = User.get_or_create(
                    uid=message.author.id)
            local, created = LocalLevel.get_or_create(
                    user=user,
                    server=server)

            level, exp = await levelup(
                    server.level,
                    server.experience)
            try:
                if level > server.level:
                    # Yay, the server leveled up
                    if server.announce_channel:
                        channel = client.get_channel(
                                f'{server.announce_channel}')
                        smsg = await client.send_message(
                            channel,
                            f"{party} {message.server.name} is now level"
                            f" {level}! {party}")
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
                    leaders = LocalLevel.select().where(
                        LocalLevel.server == server
                    ).order_by(
                        LocalLevel.level.desc(), LocalLevel.experience.desc()
                    ).limit(1)

                    if f"{leaders[0].user.uid}" == message.author.id:
                        leaderboard_roles = Role.select().where(
                            (Role.server == server) &
                            (Role.leaderboard is True)
                            ).order_by(
                                Role.awardlevel.desc()
                            )

                        leader_role = discord.utils.get(
                            message.server.roles,
                            id=f'{leaderboard_roles[0].rid}')
                        for member in message.server.members:
                            item = next(
                                (i for i in member.roles
                                 if i.id == f"{leader_role.id}"),
                                None
                            )
                            if item:
                                await client.remove_roles(member, leader_role)
                        await client.add_roles(message.author, leader_role)
                    try:
                        try:
                            role = Role.get(
                                (Role.server == server) &
                                (Role.awardlevel == level))
                        except Role.DoesNotExist as e:
                            role = None
                        if role:
                            r = discord.utils.get(message.server.roles,
                                                  id=f'{role.rid}')
                            try:
                                logger.info(f"Adding role {r.name} to "
                                            f"{message.author.name}")
                                await client.add_roles(message.author, r)
                            except AttributeError as e:
                                logger.exception(
                                    "Could not add role"
                                )
                    except Role.DoesNotExist as e:
                        logger.exception("Count not find level up reward")
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
