import discord
from discord.ext import commands
import aiohttp
import asyncio
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from others.menu import SwitchPages
from bs4 import BeautifulSoup
from typing import Any

TEST_GUILDS = [792401342969675787]

class Songs(commands.Cog):
	""" A category for commands related to finding songs. """

	def __init__(self, client) -> None:
		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)
		self.lyrics = "https://www.lyrics.com"


	@commands.Cog.listener()
	async def on_ready(self) -> None:
		print('Songs cog is online!')

	@cog_ext.cog_subcommand(
		base="find_by", name="lyrics",
		description="Searches a song by a given lyrics", options=[
			create_option(name="value", description=" The lyrics value.", option_type=3, required=True)
		], guild_ids=TEST_GUILDS
	)
	async def _lyrics(self, interaction, value: str) -> None:

		member = interaction.author


		query = await self.clean_url(value)
		req = f"{self.lyrics}/lyrics/{query}"
		async with self.session.get(req) as response:

			if response.status != 200:
				return await interaction.send(f"**Something went wrong with that search, {member.mention}!**", hidden=True)

			html = BeautifulSoup(await response.read(), 'html.parser')

			songs = html.select('.sec-lyric.clearfix')
			if not songs:
				return await interaction.send(f"**Nothing found for that search, {member.mention}!**", hidden=True)

			# Additional data:
			additional = {
				'client': self.client,
				'req': req,
				'search': value,
				'change_embed': self.make_embed
			}
			pages = SwitchPages(songs, **additional)
			await pages.start(interaction)


	async def make_embed(self, req: str, interaction: SlashContext, search: str, example: Any, offset: int, lentries: int) -> discord.Embed:
		""" Makes an embed for the current search example.
		:param req: The request URL link.
		:param interaction: The Discord context of the command.
		:param search: The search that was performed.
		:param example: The current search example.
		:param offset: The current page of the total entries.
		:param lentries: The length of entries for the given search. """

		# Makes the embed's header
		embed = discord.Embed(
			title=f"Search for __{search}__",
			description="",
			color=interaction.author.color,
			timestamp=interaction.created_at,
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
		embed.set_author(name=interaction.author, icon_url=interaction.author.avatar_url)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=interaction.guild.icon_url)

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