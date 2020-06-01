import discord
import functools
from discord.ext import commands
from collections import defaultdict
from orderedset import OrderedSet
from typing import Iterable


class TurnTracker(object):

    def __init__(self):
        self._setup()

    def _setup(self):
        self.contexts = defaultdict(OrderedSet)

    def _get_player_queue(self, context):
        return self.contexts[context]

    def with_player_queue(self, func):
        @functools.wraps(func)
        def wrapper_get_player_queue(*args, **kwargs):
            player_queue = self._get_player_queue(context)
            return func(player_queue, *args, **kwargs)
        return wrapper_do_twice

    @with_player_queue
    def reset(self, player_queue):
        player_queue.clear()

    @with_player_queue
    def advance_turn(self, player_queue):
        # Move current player to end of queue
        current_player = player_queue.pop(last=False)
        player_queue.add(current_player)

    @with_player_queue
    def get_current_player(self, player_queue):
        return player_queue[0]

    @with_player_queue
    def get_players(self, player_queue):
        return player_queue

    @with_player_queue
    def add_players(self, players: Iterable, player_queue: defaultdict) -> (list, list):
        changed_players = []
        no_changed_players = []
        for player in players:
            if player not in player_queue:
                player_queue.add(player)
                changed_players.append(player)
            else:
                no_changed_players.append(player)
        return (changed_players, no_changed_players)

    @with_player_queue
    def remove_players(self, players: Iterable, player_queue) -> (list, list):
        changed_players = []
        no_changed_players = []
        for player in players:
            if player in player_queue:
                player_queue.remove(player)
                changed_players.append(player)
            else:
                no_changed_players.append(player)
        return (changed_players, no_changed_players)


# TODO: Games per channel, not 1 per bot

class TurnTrackerCog(commands.Cog):
    """ Cog =  collection of commands, listeners, and some state """
    def __init__(self, bot):
        self.bot = bot
        self._game = TurnTracker()

    def join_member_mentions(self, seperator: str,
                             members: Iterable[discord.Member]) -> str:
        return seperator.join([member.mention for member in members])

    @commands.command(name='add', help='sign up for game')
    async def add_player(self, context: commands.Context,
                         players: commands.Greedy[discord.Member]):
        if not players:
            players = [context.author]
        new_players, existing_players = self._game.add_players(players)

        msg = ""
        if new_players:
            # user1 added to current game!
            msg += '{} added to current game!'.format(
                self.join_member_mentions(", ", new_players))
        if existing_players:
            # user2 already in game!
            already_playing_msg = "{} already in game!".format(
                self.join_member_mentions(", ", existing_players))
            if msg:
                # user1 added to current game! (user2 already in game!)
                msg += " ({})".format(already_playing_msg)
            else:
                msg = already_playing_msg
        await context.send(msg)

    @commands.command(name='remove',
                      help='remove player(s) from the current game')
    async def remove_player(self, context: commands.Context,
                            players: commands.Greedy[discord.Member]):
        if not players:
            players = [context.author]
        removed_players, not_players = self._game.remove_players(players)

        msg = ""
        if removed_players:
            # user1 removed from current game
            msg += '{} removed from current game'.format(
                self.join_member_mentions(", ", removed_players))
        if not_players:
            # user2 not in game
            not_playing_msg = "{} not in game".format(
                self.join_member_mentions(", ", not_players))
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
        players = self._game.get_players()
        if players:
            msg = 'Current players: {}'.format(
                self.join_member_mentions(", ", players))
        else:
            msg = 'No players currently signed up!'
        await context.send(msg)

    @commands.command(help='start the game')
    async def start(self, context: commands.Context):
        current_player = self._game.get_current_player()
        msg = 'Let\'s start with {}!'.format(current_player.mention)
        await context.send(msg)

    @commands.command(help='summary of the current turn of the game')
    async def status(self, context: commands.Context):
        current_player = self._game.get_current_player()
        msg = 'It is {}\'s turn'.format(current_player.mention)
        await context.send(msg)

    @commands.command(aliases=["next", "skip"],
                      help='signal that you are done with your turn')
    async def done(self, context: commands.Context):
        self._game.advance_turn()
        current_player = self._game.get_current_player()
        msg = '{}\'s turn!'.format(current_player.mention)
        await context.send(msg)

    @commands.command(help='new game')
    async def new(self, context: commands.Context):
        self._game.reset()
        await context.send("new game ready")

    @commands.command(help='reset game')
    async def reset(self, context: commands.Context):
        self._game.reset()
        await context.send("Game reset")
