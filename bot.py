import discord

class Bot():
    def __init__(self, client):
        self.commands = {}
        self.client = client

    def command(self, name, permission=discord.Permissions()):
        print(f"OUTSIDE DECORATOR - Registering command {name}")
        def decorator(f):
            print(f"Registering command {name}")
            self.commands[name] = (f, permission)
            return f
        return decorator

    async def call(self, command, message):
        handler = self.commands.get(command)
        if handler: # and message.author.server_permissions.is_subset(handler[1]):
            return await handler[0](message)
        else:
            raise ValueError(f'Command "{command}" has is not registered')
