import discord
from discord.ext import commands, menus
import aiohttp
import asyncio
from others.menu import SwitchPages
from bs4 import BeautifulSoup
from typing import Any


class Songs(commands.Cog):
	""" A category for commands related to finding songs. """

	def __init__(self, client) -> None:
		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)
		self.lyrics = "https://www.lyrics.com"


	@commands.Cog.listener()
	async def on_ready(self) -> None:
		print('Songs cog is online!')


	@commands.group(aliases=['find'])
	async def find_by(self, ctx) -> None:
		""" A command for finding songs by something. """

		if ctx.invoked_subcommand:
			return

		cmd = self.client.get_command('find_by')
		prefix = self.client.command_prefix
		subcommands = [f"{prefix}{c.qualified_name}" for c in cmd.commands
			  ]

		subcommands = '\n'.join(subcommands)
		embed = discord.Embed(
		  title="Subcommads",
		  description=f"```apache\n{subcommands}```",
		  color=ctx.author.color,
		  timestamp=ctx.message.created_at
		)
		await ctx.send(embed=embed)


	@find_by.command(hidden=True)
	async def title(self, ctx, *, value: str = None) -> None: pass

	@find_by.command()
	async def lyrics(self, ctx, *, value: str = None) -> None:
		""" Searches a song by a given lyrics.
		:param value: The lyrics value. """

		member = ctx.author

		if not value:
			return await ctx.send(f"**Please, you need to inform a `value` for your search, {member.mention}!**")


		query = await self.clean_url(value)
		req = f"{self.lyrics}/lyrics/{query}"
		async with self.session.get(req) as response:

			if response.status != 200:
				return await ctx.send(f"**Something went wrong with that search, {member.mention}!**")

			html = BeautifulSoup(await response.read(), 'html.parser')

			songs = html.select('.sec-lyric.clearfix')
			if not songs:
				return await ctx.send(f"**Nothing found for that search, {member.mention}!**")

			# Additional data:
			additional = {
				'req': req,
				'search': value,
				'change_embed': self.make_embed
			}
			await ctx.send("**Good!**")
			pages = menus.MenuPages(source=SwitchPages(songs, **additional), clear_reactions_after=True)
			await pages.start(ctx)


	async def make_embed(self, req: str, ctx: commands.Context, search: str, example: Any, offset: int, lentries: int) -> discord.Embed:
		""" Makes an embed for the current search example.
		:param req: The request URL link.
		:param ctx: The Discord context of the command.
		:param search: The search that was performed.
		:param example: The current search example.
		:param offset: The current page of the total entries.
		:param lentries: The length of entries for the given search. """

		# Makes the embed's header
		embed = discord.Embed(
			title=f"Search for __{search}__",
			description="",
			color=ctx.author.color,
			timestamp=ctx.message.created_at,
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
		embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=ctx.guild.icon_url)

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