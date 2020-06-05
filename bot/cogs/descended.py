import json
import datetime
import random
import discord
from discord.ext import commands
from collections import defaultdict
from functools import partial
from typing import Optional
from .turn_game import TurnGame, TurnGameCog


ZERO_WIDTH_SPACE = '\u200b'  # for sending 'empty' messages
PROMPT_MEASURES = {"prompt", "prompts", "card", "cards", "question",
                  "questions"}
HOUR_MEAURES = {"hour", "hours", "h"}
MINUTE_MEASURES = {"minute", "minutes", "min", "m"}


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
        self.current_prompt_index = None
        self.used_prompt_indices = set()
        self.previous_message = None
        self.maximum_prompts = 20
        self.start_time = None
        self.maximum_minutes = None
        self.end_time = None

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
        if not self.current_prompt_index:
            self._set_end_time()
            self._get_random_prompt_index()
        if self.current_prompt_index >= 0:
            return self.prompts[self.current_prompt_index]
        return self.final_prompt

    def _set_end_time(self):
        if self.maximum_minutes:
            self.end_time = datetime.datetime.now() + \
                datetime.timedelta(0, max(self.maximum_minutes, 1))

    def set_prompt_length(self, maximum_prompts):
        self.maximum_prompts = maximum_prompts

    def set_time_length(self, maximum_minutes):
        self.maximum_minutes = maximum_minutes - (2 * len(self._player_queue))

    def get_current_prompt(self):
        return self.current_prompt

    def _end_condition_met(self):
        if len(self.used_prompt_indices) >= len(self.prompts):
            # Ran out of prompts
            return True
        if self.maximum_prompts and \
           len(self.used_prompt_indices) >= self.maximum_prompts:
            # Reached maximum number of prompts
            return True
        if self.end_time:
            return datetime.datetime.now() >= self.end_time
        return False

    def _get_random_prompt_index(self):
        index = random.randrange(0, len(self.prompts) - 1)
        while index in self.used_prompt_indices:
            index = random.randrange(0, len(self.prompts) - 1)
        self.current_prompt_index = index
        self.used_prompt_indices.add(index)

    def advance_prompt(self):
        if self._end_condition_met():
            self.final_question()
            return
        self._get_random_prompt_index()

    def final_question(self):
        self.current_prompt_index = -1


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

    @commands.command(aliases=["duration"],
                      help='set length of game in either prompts, hours, or '
                           'minutes')
    async def length(self, context: commands.Context, length: float,
                     measurement: Optional[str]):
        game = self._get_game(context)
        msg_template = "Game length set to {} {}"
        if not measurement:
            msg = "Measurement required " \
                  "-- try '{length} prompts', '{length} minutes', " \
                  "or '{length} hours'".format(length=length)
        elif measurement in PROMPT_MEASURES:
            game.set_prompt_length(length)
            msg = msg_template.format(game.maximum_prompts, "prompts")
        elif measurement in HOUR_MEAURES:
            game.set_time_length(int(length * 60))
            msg = msg_template.format(game.maximum_minutes, "minutes")
        elif measurement in MINUTE_MEASURES:
            game.set_time_length(length)
            msg = msg_template.format(game.maximum_minutes, "minutes")
        else:
            msg = "Unable to understand measurement '{}' " \
                  "-- try '{length} prompts', '{length} minutes', " \
                  "or '{length} hours'".format(measurement, length=length)
        await context.send(msg)

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
