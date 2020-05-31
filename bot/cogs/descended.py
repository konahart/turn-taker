from discord.ext import commands
from .turn_taker import TurnTrackerCog


class DescendedFromTheQueen(TurnTrackerCog):
    """ Cog =  collection of commands, listeners, and some state """
    def __init__(self, bot):
        super().__init__(bot)
        self.current_prompt = 0
        self.last_message = None

    def get_prompt(self):
        c = self.current_prompt
        self.current_prompt += 1
        return c

    @commands.command(help='start the game')
    async def start(self, context: commands.Context):
        msg = '(For the Queen Intro)'
        await context.send(msg)
        await self.draw(context)

    @commands.command(aliases=["next", "prompt", "done"],
                      help='signal that you are done with your turn')
    async def draw(self, context: commands.Context):
        self._game.advance_turn()
        current_player = self._game.get_current_player()
        msg = '{}: {}'.format(self.get_prompt(), current_player.mention)
        await context.send(msg)

    @commands.command(aliases=["pass"],
                      help='pass your prompt to the next player')
    async def skip(self, context: commands.Context):
        self._game.advance_turn()
        current_player = self._game.get_current_player()
        msg = '{}: {}'.format(self.get_prompt(), current_player.mention)
        await context.send(msg)

    @commands.command(aliases=["x", "x-card", ],
                      help='signal that you are done with your turn')
    async def xcard(self, context: commands.Context):
        self._game.advance_turn()
        current_player = self._game.get_current_player()
        msg = '{}: {}'.format(self.get_prompt(), current_player.mention)
        await context.send(msg)
        await self.last_message.delete()
