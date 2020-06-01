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

    def get_players(self):
        return OrderedSet(self._player_queue)

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

    @commands.command(name='add', help='sign up for game')
    async def add_player(self, context: commands.Context,
                         players: commands.Greedy[discord.Member],
                         dummy: Optional[str]):
        if not players and dummy != "me":
            players = [context.author]
        turn_tracker = self._get_turn_tracker(context)
        new_players = []
        existing_players = []
        for player in players:
            if turn_tracker.add_player(player):
                new_players.append(player)
            else:
                existing_players.append(player)

        msg = ""
        if new_players:
            # user1 added to current game!
            msg += '{} added to current game!'.format(
                join_mentions(", ", new_players))
        if existing_players:
            # user2 already in game!
            already_playing_msg = "{} already in game!".format(
                join_mentions(", ", existing_players))
            if msg:
                # user1 added to current game! (user2 already in game!)
                msg += " ({})".format(already_playing_msg)
            else:
                msg = already_playing_msg
        await context.send(msg)

    @commands.command(name='remove',
                      help='remove player(s) from the current game')
    async def remove_player(self, context: commands.Context,
                            players: commands.Greedy[discord.Member],
                            dummy: Optional[str]):
        if not players and dummy != "me":
            players = [context.author]
        turn_tracker = self._get_turn_tracker(context)
        removed_players = []
        not_players = []
        for player in players:
            if turn_tracker.remove_player(player):
                removed_players.append(player)
            else:
                not_players.append(player)

        msg = ""
        if removed_players:
            # user1 removed from current game
            msg += '{} removed from current game'.format(
                join_mentions(", ", removed_players))
        if not_players:
            # user2 not in game
            not_playing_msg = "{} not in game".format(
                join_mentions(", ", not_players))
            if msg:
                # user1 removed from current game (user2 not in game)
                msg += " ({})".format(not_playing_msg)
            else:
                msg = not_playing_msg
        await context.send(msg)

    @commands.command(name='list',
                      help='list players of current game')
    async def list_players(self, context: commands.Context,
                           players: commands.Greedy[discord.Member]):
        turn_tracker = self._get_turn_tracker(context)
        players = turn_tracker.get_players()
        if players:
            msg = 'Current players: {}'.format(join_mentions(", ", players))
        else:
            msg = 'No players currently signed up!'
        await context.send(msg)
