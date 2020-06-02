import discord
from discord.ext import commands
from collections import defaultdict
from orderedset import OrderedSet
from typing import Optional
from .utils import join_mentions


class TurnTracker(object):

    def __init__(self, advance_func=None):
        self._player_queue = OrderedSet()
        self.advance_func = advance_func or self._default_advance_turn

    def reset(self):
        self._player_queue.clear()

    def advance_turn(self):
        self.advance_func(self._player_queue)

    @staticmethod
    def _default_advance_turn(player_queue):
        # Move current player to end of queue
        current_player = player_queue.pop(last=False)
        player_queue.add(current_player)

    def get_current_player(self):
        return self._player_queue[0]

    def get_next_player(self):
        return self._player_queue[1]

    def get_players(self):
        return OrderedSet(self._player_queue)

    def get_player_count(self):
        return len(self._player_queue)

    def add_player(self, player) -> bool:
        if player not in self._player_queue:
            self._player_queue.add(player)
            return True
        else:
            return False

    def remove_player(self, player) -> bool:
        if player in self._player_queue:
            self._player_queue.remove(player)
            return True
        else:
            return False


class TurnTrackerCog(commands.Cog):
    """ Cog =  collection of commands, listeners, and some state """
    def __init__(self, bot):
        self.bot = bot
        self._contexts = defaultdict(TurnTracker)

    def _get_turn_tracker(self, context):
        return self._contexts[context.channel.id]

    def _get_current_player(self, context):
        turn_tracker = self._get_turn_tracker(context)
        return turn_tracker.get_current_player()

    def _advance_turn(self, context):
        turn_tracker = self._get_turn_tracker(context)
        return turn_tracker.advance_turn()

    def _reset(self, context):
        turn_tracker = self._get_turn_tracker(context)
        turn_tracker.reset()

    def _get_players(self, context):
        turn_tracker = self._get_turn_tracker(context)
        return turn_tracker.get_players()

    def _update_players(self, context, players, op) -> (list, list):
        turn_tracker = self._get_turn_tracker(context)
        if op == 'add':
            change_func = turn_tracker.add_player
        elif op == 'remove':
            change_func = turn_tracker.remove_player
        else:
            print('unknown op: {}'.format(op))
            return (None, None)
        turn_tracker = self._get_turn_tracker(context)

        changed_players = []
        unchanged_players = []
        for player in players:
            if change_func(player):
                changed_players.append(player)
            else:
                unchanged_players.append(player)
        return (changed_players, unchanged_players)

    async def update_players(self, context, players, dummy, op):
        if not players:
            if not dummy or dummy == "me":
                players = [context.author]
            else:
                msg = "Sorry, I'm not able to recognize player {}! " \
                      "Try @-mentioning them or have them use `{}{}`" \
                      .format(dummy, self.bot.command_prefix, op)
                await context.send(msg)
        changed_players, unchanged_players = self._update_players(context,
                                                                  players,
                                                                  op)
        msg = ""
        if changed_players:
            changed_msg_template = '{} added to current game!' if op == 'add' \
                              else '{} removed from current game'
            changed_msg = changed_msg_template.format(
                join_mentions(", ", changed_players))
            msg = changed_msg
        if unchanged_players:
            unchanged_msg_template = "{} already in game!" if op == 'add' \
                                else "{} not in game"
            unchanged_msg = unchanged_msg_template.format(
                join_mentions(", ", unchanged_players))
            msg = "{} ({})".format(msg, unchanged_msg) if msg else \
                unchanged_msg

        if msg:
            await context.send(msg)

    @commands.command(name='add', help='sign up for game')
    async def add_player(self, context: commands.Context,
                         players: commands.Greedy[discord.Member],
                         dummy: Optional[str]):
        await self.update_players(context, players, dummy, "add")

    @commands.command(name='remove',
                      help='remove player(s) from the current game')
    async def remove_player(self, context: commands.Context,
                            players: commands.Greedy[discord.Member],
                            dummy: Optional[str]):
        await self.update_players(context, players, dummy, "remove")

    @commands.command(name='list',
                      help='list players of current game')
    async def list_players(self, context: commands.Context,
                           players: commands.Greedy[discord.Member]):
        players = self._get_players(context)
        if players:
            msg = 'Current players: {}'.format(join_mentions(", ", players))
        else:
            msg = 'No players currently signed up!'
        await context.send(msg)
