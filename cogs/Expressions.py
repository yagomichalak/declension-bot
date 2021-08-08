import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_permission
import json
import aiohttp
import os
from others.menu import SwitchPages
from typing import Any

TEST_GUILDS = [792401342969675787]

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

	@cog_ext.cog_subcommand(
		base="expression", name="french",
		description="Searches for an expression with the given word.", options=[
		create_option(name="search", description="The word you wanna look for.", option_type=3, required=True),
		], guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 15, commands.BucketType.user)
	async def french(self, interaction, search: str) -> None:

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
				return await interaction.send(f"**Nothing found, {member.mention}!**")

			data = json.loads(await response.read())

			# Additional data:
			additional = {
				'req': response,
				'search': search,
				'change_embed': self.make_french_embed
			}
			pages = SwitchPages(data, **additional)
			await pages.start(interaction)

	async def make_french_embed(self, req: str, interaction: commands.Context, search: str, example: Any, offset: int, lentries: int) -> discord.Embed:
		""" Makes an embed for the current search example.
		:param req: The request URL link.
		:param interaction: The Discord context of the command.
		:param search: The search that was performed.
		:param example: The current search example.
		:param offset: The current page of the total entries.
		:param lentries: The length of entries for the given search. """

		# Makes the embed's header
		embed = discord.Embed(
			title="__French Expression__",
			description=f"Showing results for: {example['mot']}",
			color=interaction.author.color,
			timestamp=interaction.message.created_at,
		)

		
		# General info
		embed.add_field(name="__Information__", inline=False,
			value=f"**Word:** {example['mot']}")

		# Adds a field for each example
		embed.add_field(name=f"__Expression__: {example['expression']}", value=f"**Semantique:** {example['semantique']}", inline=False)

		if context := example['contexte']:
			embed.add_field(name="__Context__", value=context, inline=False)

		# Sets the author of the search
		embed.set_author(name=interaction.author, icon_url=interaction.author.avatar_url)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=interaction.guild.icon_url)

		return embed




def setup(client) -> None:
	""" Cog's setup function. """

	client.add_cog(Expressions(client))