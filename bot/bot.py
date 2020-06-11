from discord.ext import commands
from creds import TOKEN
from cogs.descended import DescendedFromTheQueenCog


COMMAND_PREFIX = '+'


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_cog(DescendedFromTheQueenCog(self))

    async def on_ready(self):
        print('Logged in as {}#{}!'.format(self.user.name,
                                           self.user.discriminator))


def main(token):
    bot = Bot(command_prefix=COMMAND_PREFIX)
    bot.run(token)


if __name__ == "__main__":
    main(TOKEN)
