import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from googletrans import Translator
import os
import aiohttp
import json

TEST_GUILDS = [792401342969675787]

class Tools(commands.Cog):
	""" A command for tool commands. """

	def __init__(self, client) -> None:
		""" Class initializing method. """

		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)

	@commands.Cog.listener()
	async def on_ready(self) -> None:
		""" Tells when the cog is ready to use. """

		print('Tools cog is online!')


	@cog_ext.cog_slash(
		name="translate", 
		description="Translates a message into another language.", options=[
			create_option(name="language", description="The language to translate the message to..", option_type=3, required=True),
			create_option(name="message", description="The message to translate.", option_type=3, required=True),
		], guild_ids=TEST_GUILDS)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def translate(self, interaction, language: str = None, *, message: str = None):
		await interaction.defer(hidden=True)

		trans = Translator(service_urls=['translate.googleapis.com'])
		try:
			translation = trans.translate(f'{message}', dest=f'{language}')
		except ValueError:
			return await interaction.send("**Invalid parameter for 'language'!**", hidden=True)

		embed = discord.Embed(title="__Translator__",
			description=f"**Translated from `{translation.src}` to `{translation.dest}`**\n\n{translation.text}",
			color=interaction.author.color, timestamp=interaction.created_at)
		embed.set_author(name=interaction.author, icon_url=interaction.author.avatar_url)
		await interaction.send(embed=embed, hidden=True)

	@cog_ext.cog_subcommand(
		base="synonym", name="french",
		description="Searches synonyms of a French word.", options=[
			create_option(name="search", description="The word you are looking for.", option_type=3, required=True)
		], guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 15, commands.BucketType.user)
	async def synonym_french(self, interaction, search: str) -> None:

		await interaction.defer(hidden=True)
		member = interaction.author

		url = f"https://dicolink.p.rapidapi.com/mot/{search.strip().replace(' ', '%20')}/synonymes"
		querystring = {"limite":"10"}

		headers = {
			'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
			'x-rapidapi-host': "dicolink.p.rapidapi.com"
			}

		async with self.session.get(url=url, headers=headers, params=querystring) as response:
			if response.status != 200:
				return await interaction.send(f"**Nothing found, {member.mention}!**", hidden=True)

			data = json.loads(await response.read())

			# Makes the embed's header
			embed = discord.Embed(
				title="__French Synonyms__",
				description=f"Showing results for: {search}",
				color=member.color,
				timestamp=interaction.created_at,
			)

			words = ', '.join(list(map(lambda w: f"**{w['mot']}**", data)))

			# Adds a field for each example
			embed.add_field(name=f"__Words__", value=words, inline=False)

			# Sets the author of the search
			embed.set_author(name=member, icon_url=member.avatar_url)
			await interaction.send(embed=embed, hidden=True)


	@cog_ext.cog_subcommand(
		base="antonym", name="french",
		description="Searches antonyms of a French word", options=[
			create_option(name="search", description="The word you are looking for.", option_type=3, required=True)
		], guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 15, commands.BucketType.user)
	async def antonym_french(self, interaction, search: str) -> None:

		await interaction.defer(hidden=True)
		member = interaction.author

		url = f"https://dicolink.p.rapidapi.com/mot/{search.strip().replace(' ', '%20')}/antonymes"
		querystring = {"limite":"10"}

		headers = {
			'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
			'x-rapidapi-host': "dicolink.p.rapidapi.com"
			}

		async with self.session.get(url=url, headers=headers, params=querystring) as response:
			if response.status != 200:
				return await interaction.send(f"**Nothing found, {member.mention}!**", hidden=True)

			data = json.loads(await response.read())

			# Makes the embed's header
			embed = discord.Embed(
				title="__French Antonyms__",
				description=f"Showing results for: {search}",
				color=member.color,
				timestamp=interaction.created_at,
			)

			words = ', '.join(list(map(lambda w: f"**{w['mot']}**", data)))

			# Adds a field for each example
			embed.add_field(name=f"__Words__", value=words, inline=False)

			# Sets the author of the search
			embed.set_author(name=member, icon_url=member.avatar_url)
			await interaction.send(embed=embed, hidden=True)



def setup(client) -> None:
	""" Cog's setup function. """

	client.add_cog(Tools(client))