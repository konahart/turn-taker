import json
import datetime
import random
import discord
from discord.ext import commands
from collections import defaultdict
from functools import partial
from typing import Optional
from .turn_game import TurnGame, TurnGameCog
from .load_gsheet import load_sheet


ZERO_WIDTH_SPACE = '\u200b'  # for sending 'empty' messages
PROMPT_MEASURES = {"prompt", "prompts", "card", "cards", "question",
                   "questions"}
HOUR_MEAURES = {"hour", "hours", "h"}
MINUTE_MEASURES = {"minute", "minutes", "min", "m"}
DEFAULT_GAME_LENGTH = 20  # prompts


class DescendedGameData(object):
    def __init__(self, game_file=None, game_url=None):
        if game_file:
            with open(game_file, 'r') as f:
                data = json.load(f)
        elif game_url:
            data = load_sheet(game_url)
        else:
            data = {}
        self.title = data.get("title", "")
        self.intro = data.get("intro", "")
        self.instructions = data.get("instructions", [])
        self.final_question = data.get("final", "")
        self.prompts = data.get("prompts", [])


class DescendedGame(TurnGame):
    def __init__(self, game_data):
        super().__init__()
        self._game_data = game_data
        self.current_prompt_index = None
        self.used_prompt_indices = set()
        self.previous_message = None
        self.maximum_prompts = None
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
            self._set_end_condition()
            self._get_random_prompt_index()
        if self.current_prompt_index >= 0:
            return self.prompts[self.current_prompt_index]
        return self.final_prompt

    def _set_end_condition(self):
        if self.maximum_minutes:
            self.end_time = datetime.datetime.now() + \
                datetime.timedelta(0, max(self.maximum_minutes, 1))
        if not self.maximum_prompts:
            self.maximum_prompts = DEFAULT_GAME_LENGTH

    def _end_condition_met(self):
        if len(self.used_prompt_indices) >= len(self.prompts):
            # Ran out of prompts
            return True
        if self.maximum_prompts and \
           len(self.used_prompt_indices) >= self.maximum_prompts:
            # Reached maximum number of prompts
            return True
        if self.end_time:
            # End time has elapsed
            return datetime.datetime.now() >= self.end_time
        return False

    def set_prompt_length(self, maximum_prompts):
        self.maximum_prompts = int(maximum_prompts)

    def set_time_length(self, maximum_minutes):
        self.maximum_minutes = int(maximum_minutes -
                                   (2 * len(self._player_queue)))

    def get_end_conditions(self):
        end_conditions = []
        if self.maximum_prompts:
            end_conditions.append("{} prompts".format(self.maximum_prompts))
        if self.maximum_minutes:
            end_conditions.append("{} minutes".format(self.maximum_minutes))
        if not end_conditions:
            end_conditions.append("{} prompts (default)"
                                  .format(DEFAULT_GAME_LENGTH))
        return end_conditions

    def get_current_prompt(self):
        return self.current_prompt

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

    def __init__(self, bot, game_file=None):
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
    async def length(self, context: commands.Context, length: Optional[float],
                     measurement: Optional[str]):
        game = self._get_game(context)
        msg_template = "Game length set to {} {}"
        if not length:
            end_conditions = game.get_end_conditions()
            msg = msg_template.format(", or ".join(end_conditions), "")
            await context.send(msg)
            return
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

    @commands.command(help='load game from a Google sheet')
    async def load(self, context: commands.Context, url):
        if not isinstance(url, str):
            msg = "Must provide url of Google Sheet to load from"
        new_game_data = DescendedGameData(game_url=url)
        self._contexts[context.channel.id] = DescendedGame(new_game_data)
        game = self._get_game(context)
        msg = f"'{game.title}' loaded from url"
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
        content = game.last_message.content
        xCardMessage = f"[this prompt was X-Carded :heart: ] ||{content}||"
        await game.last_message.edit(content=xCardMessage)
        # replace with new prompt
        game.advance_prompt()
        await self._send_prompt(context)
