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

    def _send_prompt(self, context: commands.Context):
        player = self._get_current_player(context)
        msg = '{}: {}'.format(player.mention, self.get_prompt())
        await context.send(msg)

    @commands.command(aliases=['instructions'])
    async def intro(self, context: commands.Context):
        msg = '(For the Queen Intro)'
        await context.send(msg)
        msg = 'Whoever wishes to may start, by using `{}start`'.format(
            self.bot.command_prefix)
        await context.send(msg)

    @commands.command(help='start the game')
    async def start(self, context: commands.Context):
        first_player = context.author
        turn_tracker = self._get_turn_tracker(context)
        turn_tracker.fast_forward(first_player)
        await self._send_prompt(context)

    @commands.command(aliases=["next", "prompt", "done"],
                      help='signal that you are done with your turn')
    async def draw(self, context: commands.Context):
        turn_tracker = self._get_turn_tracker(context)
        turn_tracker.advance_turn()
        await self._send_prompt(context)

    @commands.command(aliases=["pass"],
                      help='pass your prompt to the next player')
    async def skip(self, context: commands.Context):
        self._game.advance_turn()
        current_player = self._game.get_current_player()
        msg = '{}, we\'d like to hear your answer to the question: {}'.format(
            current_player.mention, self.current_prompt)
        await context.send(msg)

    @commands.command(aliases=["x", "x-card", ],
                      help='signal that you are done with your turn')
    async def xcard(self, context: commands.Context):
        self._game.advance_turn()
        current_player = self._game.get_current_player()
        msg = '{}: {}'.format(current_player.mention, self.get_prompt())
        await context.send(msg)
        await self.last_message.delete()
