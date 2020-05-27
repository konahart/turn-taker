from discord.ext.commands import Bot
from creds import TOKEN
from cogs.descended import DescendedFromTheQueen

COMMAND_PREFIX = '+'

bot = Bot(command_prefix=COMMAND_PREFIX)
bot.add_cog(DescendedFromTheQueen(bot))


@bot.event
async def on_ready():
    print('Logged in as {}#{}!'.format(bot.user.name, bot.user.discriminator))


def main():
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
