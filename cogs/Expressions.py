from ctypes import Union
import discord
from discord.ext import commands
from discord import ApplicationContext, slash_command, Option, SlashCommandGroup

import json
import aiohttp
import os

from typing import Any, Union, Dict
from others.views import PaginatorView
from others import utils

TEST_GUILDS = [777886754761605140]

class Expressions(commands.Cog):
	""" A category for commands related to language 
	expression acquisition. """

	def __init__(self, client) -> None:
		""" Class initializing method. """

		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)

	_expression = SlashCommandGroup("expression", "Searches for an expression in a given language.", guild_ids=TEST_GUILDS)

	@commands.Cog.listener()
	async def on_ready(self) -> None:
		""" Tells when the cog is ready to use. """

		print('Expression cog is online!')

	@_expression.command(name="french")
	@commands.cooldown(1, 15, commands.BucketType.user)
	async def _expression_french(self, interaction, search: Option(str, name="search", description="The word you wanna look for.", required=True)) -> None:
		""" Searches for an expression with the given word. """

		await interaction.defer(ephemeral=True)
		member = interaction.author

		url = f"https://dicolink.p.rapidapi.com/mot/{search.strip().replace(' ', '%20')}/expressions"

		querystring = {"limite": "10"}

		headers = {
			'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
			'x-rapidapi-host': "dicolink.p.rapidapi.com"
			}

		async with self.session.get(url=url, headers=headers, params=querystring) as response:

			if response.status != 200:
				self.french.reset_cooldown(interaction)
				return await interaction.respond(f"**Nothing found, {member.mention}!**", ephemeral=True)

			data = json.loads(await response.read())

			# Additional data:
			additional = {
				'req': response,
				'search': search,
				'change_embed': self.make_french_embed
			}
			view = PaginatorView(data, **additional)
			embed = await view.make_embed(interaction.author)
			await interaction.respond(embed=embed, view=view)

	async def make_french_embed(self, req: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
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
			title="__French Expression__",
			description=f"Showing results for: {example['mot']}",
			color=member.color,
			timestamp=current_time,
		)
		
		# General info
		embed.add_field(name="__Information__", inline=False,
			value=f"**Word:** {example['mot']}")

		# Adds a field for each example
		embed.add_field(name=f"__Expression__: {example['expression']}", value=f"**Semantique:** {example['semantique']}", inline=False)

		if context := example['contexte']:
			embed.add_field(name="__Context__", value=context, inline=False)

		# Sets the author of the search
		embed.set_author(name=member, icon_url=member.display_avatar)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=member.guild.icon.url)

		return embed




def setup(client) -> None:
	""" Cog's setup function. """

	client.add_cog(Expressions(client))