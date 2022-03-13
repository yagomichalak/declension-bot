import discord
from discord.ext import commands
from discord import Option, slash_command, SlashCommandGroup, ApplicationContext

import aiohttp
import asyncio
from bs4 import BeautifulSoup

from others import utils
from others.views import PaginatorView
from typing import Any, Union, Dict

TEST_GUILDS = [777886754761605140]

class Songs(commands.Cog):
	""" A category for commands related to finding songs. """

	def __init__(self, client) -> None:
		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)
		self.lyrics = "https://www.lyrics.com"

	_find_by = SlashCommandGroup('find_by', "Searches a song")#, guild_ids=TEST_GUILDS)

	@commands.Cog.listener()
	async def on_ready(self) -> None:
		print('Songs cog is online!')

	@_find_by.command(name="lyrics")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def _find_by_lyrics(self, interaction, value: Option(str, name="value", description=" The lyrics value.", required=True)) -> None:
		""" Searches a song by a given lyrics. """

		member = interaction.author
		await interaction.defer(ephemeral=True)

		query = await self.clean_url(value)
		req = f"{self.lyrics}/lyrics/{query}"
		async with self.session.get(req) as response:

			if response.status != 200:
				return await interaction.respond(f"**Something went wrong with that search, {member.mention}!**", ephemeral=True)

			html = BeautifulSoup(await response.read(), 'html.parser')

			songs = html.select('.sec-lyric.clearfix')
			if not songs:
				return await interaction.respond(f"**Nothing found for that search, {member.mention}!**", ephemeral=True)

			# Additional data:
			additional = {
				'client': self.client,
				'req': req,
				'search': value,
				'change_embed': self.make_embed
			}
			view = PaginatorView(songs, **additional)
			embed = await view.make_embed(interaction.author)
			await interaction.respond(embed=embed, view=view)

	async def make_embed(self, req: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
		offset: int, lentries: int, entries: Dict[str, Any], title: str = None, result: str = None) -> discord.Embed:
		""" Makes an embed for the current search example.
		:param req: The request URL link.
		:param member: The member who triggered the command.
		:param search: The search that was performed.
		:param example: The current search example.
		:param offset: The current page of the total entries.
		:param lentries: The length of entries for the given search.
		:param entries: The entries of the search.
		:param title: The title of the search.
		:param result: The result of the search. """

		current_time = await utils.get_time_now()

		# Makes the embed's header
		embed = discord.Embed(
			title=f"Search for __{search}__",
			description="",
			color=member.color,
			timestamp=current_time,
			url=req
			)

		title = example.select_one('.lyric-meta.within-lyrics')
		href = h if (h := example.select_one('.lyric-meta-title a')['href']) else None
		embed.add_field(
			name="__Title__", 
			value=f"[{title.get_text().strip()}]({self.lyrics}/{href})")

		image = img['src'] if (img := example.select_one('.album-thumb img')) else ''
		
		if image.startswith('https://'):
			embed.set_thumbnail(url=image)
	
		# Sets the author of the search
		embed.set_author(name=member, icon_url=member.display_avatar)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=member.guild.icon.url)

		return embed

	async def clean_url(self, url: str) -> str:
		""" Cleans the url link by replacing special characters with an url equivalent characters. 
		:param url: The url to clean. """

		url = url.replace(' ', '%20'
			).replace(',', '%2C'
			).replace("'", '%27'
			).replace('!', '%21'
			).replace(':', '%3A'
			).replace(';', '%3B'
			).replace('>', '%26gt%3B'
			).replace('\\', '%5C'
			).replace('/', '%2F'
			).replace('|', '%7C'
			).replace('#', '%23'
			).replace('$', '%24'
			).replace('%', '%25'
			).replace('&', '%26'
			).replace('*', '%2A'
			).replace('(', '%28'
			).replace(')', '%29'
			).replace('[', '%5B'
			).replace(']', '%5D'
			).replace('{', '%7B'
			).replace('}', '%7D')

		return url


def setup(client) -> None:
	client.add_cog(Songs(client))