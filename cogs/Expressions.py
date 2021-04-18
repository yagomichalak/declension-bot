import discord
from discord.ext import commands, menus
import json
import aiohttp
import os
from others.menu import SwitchPages
from typing import Any


class Expressions(commands.Cog):
	""" A category for commands related to language 
	expression acquisition. """

	def __init__(self, client) -> None:
		""" Class initializing method. """

		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)

	@commands.Cog.listener()
	async def on_ready(self) -> None:
		""" Tells when the cog is ready to use. """

		print('Expression cog is online!')

	@commands.group(aliases=['xp', 'exp'])
	async def expression(self, ctx) -> None:
		""" A command for getting expressions in specific languages. """

		if ctx.invoked_subcommand:
		  return

		cmd = self.client.get_command('expression')
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


	@expression.command(aliases=['fr', 'français', 'francês', 'francés', 'frances'])
	@commands.cooldown(1, 15, commands.BucketType.user)
	async def french(self, ctx, *, search: str = None) -> None:
		""" Searches for an expression with the given word.
		:param search: The word you wanna look for.```
	
		🇫🇷-🇧🇪 __**Example:**__
		```ini\n[1] dec!expression fr cheval\n[2] dec!exp french canard """


		member = ctx.author

		if not search:
			return await ctx.send(f"**Please, {member.mention}, inform a word!**")


		url = f"https://dicolink.p.rapidapi.com/mot/{search}/expressions"

		querystring = {"limite": "10"}

		headers = {
			'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
			'x-rapidapi-host': "dicolink.p.rapidapi.com"
			}

		async with self.session.get(url=url, headers=headers, params=querystring) as response:

			if response.status != 200:
				return await ctx.send(f"**Something went wrong with that search, {member.mention}!**")

			data = json.loads(await response.read())

			# Additional data:
			additional = {
				'req': response,
				'search': search,
				'change_embed': self.make_french_embed
			}
			pages = menus.MenuPages(source=SwitchPages(data, **additional), clear_reactions_after=True)
			await pages.start(ctx)

	async def make_french_embed(self, req: str, ctx: commands.Context, search: str, example: Any, offset: int, lentries: int) -> discord.Embed:
		""" Makes an embed for the current search example.
		:param req: The request URL link.
		:param ctx: The Discord context of the command.
		:param search: The search that was performed.
		:param example: The current search example.
		:param offset: The current page of the total entries.
		:param lentries: The length of entries for the given search. """

		# Makes the embed's header
		embed = discord.Embed(
			title="__French Dictionary__",
			description=f"Showing results for: {example['mot']}",
			color=ctx.author.color,
			timestamp=ctx.message.created_at,
		)

		
		# General info
		embed.add_field(name="__Information__", inline=False,
			value=f"**Word:** {example['mot']}")

		# Adds a field for each example
		embed.add_field(name=f"__Expression__: {example['expression']}", value=f"**Semantique:** {example['semantique']}", inline=False)

		if context := example['contexte']:
			embed.add_field(name="__Context__", value=context, inline=False)

		# Sets the author of the search
		embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=ctx.guild.icon_url)

		return embed




def setup(client) -> None:
	""" Cog's setup function. """

	client.add_cog(Expressions(client))