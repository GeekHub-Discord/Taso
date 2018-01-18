import discord
from main import get_logger

logger = get_logger()

class Bot():
    def __init__(self, client):
        self.commands = {}
        self.client = client

    def command(self, name, permission=discord.Permissions()):
        def decorator(f):
            logger.info(f"Registering command {name}")
            self.commands[name] = (f, permission)
            return f
        return decorator

    async def call(self, command, message):
        handler = self.commands.get(command)
        if handler:
            if message.author.server_permissions >= handler[1]:
                return await handler[0](message)
            raise ValueError(f"Not enough permissions for {command}")
        else:
            raise ValueError(f'Command "{command}" has is not registered')
