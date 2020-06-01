import discord
from typing import Iterable


def join_mentions(seperator: str, members: Iterable[discord.Member]) -> str:
    return seperator.join([member.mention for member in members])
