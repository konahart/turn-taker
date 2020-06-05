import json
import random
import discord
from discord.ext import commands
from collections import defaultdict
from functools import partial
from .turn_game import TurnGame, TurnGameCog


ZERO_WIDTH_SPACE = '\u200b'  # for sending 'empty' messages


class DescendedGameData(object):
    def __init__(self, game_file):
        with open(game_file, 'r') as f:
            data = json.load(f)
        self.title = data["title"]
        self.intro = data["intro"]
        self.instructions = data["instructions"]
        self.final_question = data["final"]
        self.prompts = data["prompts"]


class DescendedGame(TurnGame):
    def __init__(self, game_data):
        super().__init__()
        self._game_data = game_data
        self.used_prompts = set()
        self.current_prompt_index = 0
        self.previous_message = None

    @property
    def title(self):
        return self._game_data.title

    @property
    def intro(self):
        return self._game_data.intro

    @property
    def instructions(self):
        return self._game_data.instructions

    @property
    def final_prompt(self):
        return self._game_data.final_question

    @property
    def prompts(self):
        return self._game_data.prompts

    @property
    def current_prompt(self):
        return self.prompts[self.current_prompt_index]

    def get_current_prompt(self):
        return self.current_prompt

    def advance_prompt(self):
        if len(self.used_prompts) > len(self.prompts):
            # Ran out of prompts, end the game
            self.final_question()
            return
        index = random.randrange(0, len(self.prompts) - 1)
        while index in self.used_prompts:
            index = random.randrange(0, len(self.prompts) - 1)
        self.current_prompt_index = index
        self.used_prompts.add(index)

    def final_question(self):
        pass


class DescendedFromTheQueenCog(TurnGameCog):
    """ Cog =  collection of commands, listeners, and some state """
    def __init__(self, bot, game_file):
        super().__init__(bot)
        self.game_data = DescendedGameData(game_file)
        self._contexts = defaultdict(partial(DescendedGame, self.game_data))

    async def _send_game_msg(self, context: commands.Context, msg, game=None):
        if not game:
            game = self._get_game(context)
        game.last_message = await context.send(msg)

    async def _send_prompt(self, context: commands.Context):
        game = self._get_game(context)
        player = game.get_current_player()
        prompt = game.get_current_prompt()
        msg = '{}: {}'.format(player.mention, prompt)
        await self._send_game_msg(context, msg, game=game)

    @commands.command(aliases=['instructions'])
    async def intro(self, context: commands.Context):
        game = self._get_game(context)
        embed = discord.Embed(title=game.title,
                              colour=discord.Colour(0x3094ec),
                              description="_{}_"
                              .format("\n\n".join(game.intro)))
        await context.send(content=ZERO_WIDTH_SPACE, embed=embed)
        msg = 'Whoever wishes to may start, by using `{}start`' \
              .format(self.bot.command_prefix)
        await context.send(msg)

    @commands.command(help='start the game')
    async def start(self, context: commands.Context):
        first_player = context.author
        game = self._get_game(context)
        game.fast_forward(first_player)
        await self._send_prompt(context)

    @commands.command(aliases=["next", "prompt", "done"],
                      help='signal that you are done with your turn')
    async def draw(self, context: commands.Context):
        game = self._get_game(context)
        game.advance_turn()
        game.advance_prompt()
        await self._send_prompt(context)

    @commands.command(aliases=["pass"],
                      help='pass your prompt to the next player')
    async def skip(self, context: commands.Context):
        game = self._get_game(context)
        game.advance_turn()
        current_player = game.get_current_player()
        msg = '{}, we\'d like to hear your answer to the question: {}'.format(
            current_player.mention, game.get_current_prompt())
        await context.send(msg)

    @commands.command(aliases=["x", "x-card", "discard"],
                      help='remove the previous prompt from the game')
    async def xcard(self, context: commands.Context):
        game = self._get_game(context)
        xCardMessage = "[this prompt was X-Carded :heart: ]"
        await game.last_message.edit(content=xCardMessage)
        # replace with new prompt
        game.advance_prompt()
        await self._send_prompt(context)
