import discord
from discord.ext import commands
from googletrans import Translator
import os
import aiohttp
import json


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


	@commands.command(aliases=['t', 'trans'])
	async def translate(self, ctx, language: str = None, *, message: str = None):
		""" Translates a message into another language.
		:param language: The language to translate the message to.
		:param message: The message to translate.
		:return: A translated message. """

		await ctx.message.delete()
		if not language:
			return await ctx.send("**Please, inform a language!**", delete_after=5)
		elif not message:
			return await ctx.send("**Please, inform a message to translate!**", delete_after=5)

		trans = Translator(service_urls=['translate.googleapis.com'])
		try:
			translation = trans.translate(f'{message}', dest=f'{language}')
		except ValueError:
			return await ctx.send("**Invalid parameter for 'language'!**", delete_after=5)
		embed = discord.Embed(title="__Translator__",
							  description=f"**Translated from `{translation.src}` to `{translation.dest}`**\n\n{translation.text}",
							  colour=ctx.author.color, timestamp=ctx.message.created_at)
		embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
		await ctx.send(embed=embed)

	@commands.group(aliases=['syn'])
	async def synonym(self, ctx) -> None:
		""" A command for getting synonyms of words in specific languages. """

		if ctx.invoked_subcommand:
			return

		cmd = self.client.get_command('synonym')
		prefix = self.client.command_prefix
		subcommands = [f"{prefix}{c.qualified_name}" for c in cmd.commands]
		subcommands = '\n'.join(subcommands)

		embed = discord.Embed(
			title="Subcommads",
			description=f"```apache\n{subcommands}```",
			color=ctx.author.color,
			timestamp=ctx.message.created_at
		)
		await ctx.send(embed=embed)

	@synonym.command(name='french', aliases=['fr', 'français', 'francês', 'francés', 'frances'])
	@commands.cooldown(1, 15, commands.BucketType.user)
	async def synonym_french(self, ctx, *, search: str = None) -> None:
		""" Searches synonyms of a French word.
		:param search: The word you are looking for.```

		🇫🇷-🇧🇪 __**Example:**__
		```ini\n[1] dec!synonym fr autre\n[2] dec!syn french différent """

		member = ctx.author

		if not search:
			self.synonym_french.reset_cooldown(ctx)
			return await ctx.send(f"**Please, {member.mention}, inform a word!**")


		url = f"https://dicolink.p.rapidapi.com/mot/{search.strip().replace(' ', '%20')}/synonymes"
		querystring = {"limite":"10"}

		headers = {
			'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
			'x-rapidapi-host': "dicolink.p.rapidapi.com"
			}

		async with self.session.get(url=url, headers=headers, params=querystring) as response:
			if response.status != 200:
				self.synonym_french.reset_cooldown(ctx)
				return await ctx.send(f"**Nothing found, {member.mention}!**")

			print('aa')
			data = json.loads(await response.read())
			print('bb')

			# Makes the embed's header
			embed = discord.Embed(
				title="__French Synonyms__",
				description=f"Showing results for: {search}",
				color=member.color,
				timestamp=ctx.message.created_at,
			)

			words = ', '.join(list(map(lambda w: f"**{w['mot']}**", data)))

			# Adds a field for each example
			embed.add_field(name=f"__Words__", value=words, inline=False)

			# Sets the author of the search
			embed.set_author(name=member, icon_url=member.avatar_url)
			await ctx.send(embed=embed)

	@commands.group(aliases=['ant'])
	async def antonym(self, ctx) -> None:
		""" A command for getting antonyms of words in specific languages. """

		if ctx.invoked_subcommand:
			return

		cmd = self.client.get_command('antonym')
		prefix = self.client.command_prefix
		subcommands = [f"{prefix}{c.qualified_name}" for c in cmd.commands]
		subcommands = '\n'.join(subcommands)

		embed = discord.Embed(
			title="Subcommads",
			description=f"```apache\n{subcommands}```",
			color=ctx.author.color,
			timestamp=ctx.message.created_at
		)
		await ctx.send(embed=embed)

	@antonym.command(name='french', aliases=['fr', 'français', 'francês', 'francés', 'frances'])
	@commands.cooldown(1, 15, commands.BucketType.user)
	async def antonym_french(self, ctx, *, search: str = None) -> None:
		""" Searches antonyms of a French word.
		:param search: The word you are looking for.```

		🇫🇷-🇧🇪 __**Example:**__
		```ini\n[1] dec!antonym fr autre\n[2] dec!ant french différent """

		member = ctx.author

		if not search:
			self.antonym_french.reset_cooldown(ctx)
			return await ctx.send(f"**Please, {member.mention}, inform a word!**")


		url = f"https://dicolink.p.rapidapi.com/mot/{search.strip().replace(' ', '%20')}/antonymes"
		querystring = {"limite":"10"}

		headers = {
			'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
			'x-rapidapi-host': "dicolink.p.rapidapi.com"
			}

		async with self.session.get(url=url, headers=headers, params=querystring) as response:
			if response.status != 200:
				self.antonym_french.reset_cooldown(ctx)
				return await ctx.send(f"**Nothing found, {member.mention}!**")

			print('aa')
			data = json.loads(await response.read())
			print('bb')

			# Makes the embed's header
			embed = discord.Embed(
				title="__French Antonyms__",
				description=f"Showing results for: {search}",
				color=member.color,
				timestamp=ctx.message.created_at,
			)

			words = ', '.join(list(map(lambda w: f"**{w['mot']}**", data)))

			# Adds a field for each example
			embed.add_field(name=f"__Words__", value=words, inline=False)

			# Sets the author of the search
			embed.set_author(name=member, icon_url=member.avatar_url)
			await ctx.send(embed=embed)



def setup(client) -> None:
	""" Cog's setup function. """

	client.add_cog(Tools(client))