import discord
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_option, create_choice, create_permission
from discord_slash.model import CogBaseCommandObject
import os
import asyncio
from re import match
from itertools import cycle
from others.customerrors import NotInWhitelist
from dotenv import load_dotenv
load_dotenv()

TEST_GUILDS = [792401342969675787]

status = cycle([
	"Russian declensions", "German declensions", "Finnish declensions", "Polish declensions",
	"English conjugations", "Spanish conjugations",
	"French conjugations", "Italian conjugations",
	"Portuguese conjugations", "Arabic conjugations",
	"Japanese conjugations", "Dutch conjugations",
	"Polish conjugations", "German conjugations",
	"Esperanto conjugations", "Estonian conjugations",
	"Turkish conjugations", "Danish conjugations",
	"Swedish conjugations", "Norwegian conjugations",
	"Faroese conjugations", "Icelandic conjugations",
	"Indonesian conjugations", "Thai conjugations",
	"Maltese conjugations", "Malay conjugations",
	"Vietnamese conjugations", "Finnish conjugations",
	"Russian conjugations", "Romanian conjugations",
	"Catalan conjugations", "Greek conjugations",
	"Afrikaans conjugations", "Lithuanian conjugations", 
	"Latvian conjugations", "Macedonian conjugations",
	"Persian conjugations", "Hebrew conjugations",
	"Spanish context", "French context",
	"Italian context", "German context"
	])

intents = discord.Intents.default()
client = commands.Bot(command_prefix='dec!', intents=intents)
slash = SlashCommand(client, sync_commands=True, sync_on_cog_reload=True)
client.remove_command('help')
token = os.getenv('TOKEN')
on_guild_log_id = os.getenv('ON_GUILD_LOG_ID')

@client.event
async def on_ready():
	change_status.start()
	print("Bot is ready!")


@tasks.loop(seconds=30)
async def change_status():
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"{next(status)}!"))

@client.event
async def on_command_error(ctx, error):
	""" Error handler. """
	
	if isinstance(error, commands.MissingPermissions):
		await ctx.send(error)

	elif isinstance(error, commands.BotMissingPermissions):
		await ctx.send("**I don't have permissions to run this command!**")

	elif isinstance(error, commands.BadArgument):
		await ctx.send("**Invalid parameters!**")

	elif isinstance(error, commands.CommandOnCooldown):
		secs = error.retry_after
		if int(secs) >= 60:
			await ctx.send(f"You are on cooldown! Try again in {secs/60:.1f} minutes!")
		else:
			await ctx.send(error)
			
	elif isinstance(error, commands.NotOwner):
		await ctx.send("**You can't do that, you're not the owner!**")

	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('**Make sure to inform all parameters!**')

	elif isinstance(error, NotInWhitelist):
		await ctx.send(f"**{error}**")
	else:
		print(error)

@client.event
async def on_slash_command_error(ctx, error) -> None:

	if isinstance(error, commands.CommandOnCooldown):
		secs = int(float(error.retry_after))
		await ctx.send(content=f"You are on cooldown! Try again in {secs} seconds!", hidden=True)


@client.event
async def on_message(message):
	if message.author.bot:
		return
	if match(f"<@!?{client.user.id}>", message.content) is not None:
		await message.channel.send(f"**{message.author.mention}, my prefix is `{client.command_prefix}`**")

	await client.process_commands(message)


@client.event
async def on_guild_join(guild):
	general = guild.system_channel
	embed = discord.Embed(
			title="Hello learners!",
			description=f"{len(client.guilds)}# Let us decline some words! Thank you for the hospitality, **{guild.name}**!",
			color=client.user.color
			)

	# Sends an embedded message in the new server
	if general and general.permissions_for(guild.me).send_messages:
		try:
			await general.send(embed=embed)
		except Exception:
			print('No perms to send a welcome message!')

	#Logs it in the bot's support server on_guild log
	guild_log = client.get_channel(int(on_guild_log_id))
	if guild_log:
		embed.set_thumbnail(url=guild.icon_url)
		await guild_log.send(embed=embed)
	

@client.event
async def on_guild_remove(guild):
	embed = discord.Embed(title="Goodbye world!",
			description=f"Our server number {len(client.guilds)+1}, called **{guild.name}**, gave up on declining languages... LOL!",
			color=discord.Color.red()
			)
	embed.set_thumbnail(url=guild.icon_url)
	#Logs it in the bot's support server's on_guild log
	guild_log = client.get_channel(int(on_guild_log_id))
	if guild_log:
		await guild_log.send(embed=embed)

@slash.slash(name="ping", description="Shows the bot's latency.", guild_ids=TEST_GUILDS)
async def ping(ctx):

	await ctx.send(f"**Ping: __{round(client.latency * 1000)}__ ms**", hidden=True)


@slash.slash(name="info", description="Shows some information about the bot itself.", guild_ids=TEST_GUILDS)
# @commands.cooldown(1, 10, type=commands.BucketType.guild)
async def info(ctx):

	embed = discord.Embed(title='Declinator Bot', description="__**WHAT IS IT?:**__```Hello, the Declinator bot is an open source bot based on word declensions, verb conjugations and words in context.\nPS: declensions are all forms of a word in a language that contains a grammatical case system.```", colour=ctx.author.color, url="http://193.70.127.179/", timestamp=ctx.created_at)
	embed.add_field(name="📚 __**Language declinators**__",
								value="So far, there are `4` different languages to decline, `34` to conjugate and `4` to get context.",
								inline=True)
	embed.add_field(name="💻 __**Programmed in**__",
								value="The Declinator bot was built in Python, and you can find its GitHub repository [here](https://github.com/yagomichalak/declension-bot).",
								inline=True)
	embed.add_field(name='❓ __**How do you do It?**__',
								value="The bot either web scrapes or uses an API to fetch information from websites, after that, the bot does its magic to nicely show the information in an embedded message.",
								inline=True)
	embed.add_field(name="🌎 __**More languages**__ ", 
								value="More languages will be added as I'm requested and have some time to implement them.", inline=True)
	embed.set_footer(text=ctx.guild.name,
								icon_url='https://cdn.discordapp.com/icons/459195345419763713/a_dff4456b872c84146a78be8422e33cc2.gif?size=1024')
	embed.set_thumbnail(
		url=client.user.avatar_url)
	embed.set_author(name='DNK#6725', url='https://discord.gg/languages',
								icon_url='https://cdn.discordapp.com/attachments/719020754858934294/720289112040669284/DNK_icon.png')
	await ctx.send(embed=embed, hidden=True)

@slash.slash(name="invite", description="SSends the bot's invite.", guild_ids=TEST_GUILDS)
async def invite(ctx):

	invite = 'https://discord.com/api/oauth2/authorize?client_id=753754955005034497&permissions=59456&scope=bot'
	await ctx.send(f"Here's my invite:\n{invite}", hidden=True)

@client.command()
async def help(ctx, *, cmd: str = None):
	""" Shows some information about commands and categories. """
	
	if not cmd:
			embed = discord.Embed(
			title="All commands and categories",
			description=f"```ini\nUse {client.command_prefix}help command or {client.command_prefix}help category to know more about a specific command or category\n\n[Examples]\n[1] Category: {client.command_prefix}help Declension\n[2] Command : {client.command_prefix}help spanish```",
			timestamp=ctx.created_at,
			color=ctx.author.color
			)

			for cog in client.cogs:
					cog = client.get_cog(cog)
					commands = [c.qualified_name for c in cog.get_commands() if not c.hidden]
					subcommands = []
					for c in cog.get_commands():
							try:
								for sb in c.commands:
									if not c.hidden:
										subcommands.append(sb.qualified_name)
							except AttributeError:
								pass

					if commands:
						text = f"`Commands:` {', '.join(commands)}" 
						if subcommands:
							text += f"\n`Subcommands:` {', '.join(subcommands)}"
						embed.add_field(
						name=f"__{cog.qualified_name}__",
						value=text,
						inline=False
						)

			cmds = []
			for y in client.walk_commands():
					if not y.cog_name and not y.hidden:
							cmds.append(y.name)
			embed.add_field(
			name='__Uncategorized Commands__', 
			value=f"`Commands:` {', '.join(cmds)}", 
			inline=False)
			await ctx.send(embed=embed)

	else:
		# Checks if it's a command
		if command := client.get_command(cmd.lower()):
			command_embed = discord.Embed(title=f"__Command:__ {command.name}", description=f"__**Description:**__\n```{command.help}```", color=ctx.author.color, timestamp=ctx.created_at)
			return await ctx.send(embed=command_embed)

		for cog in client.cogs:
			if str(cog).lower() == str(cmd).lower():
					cog = client.get_cog(cog)
					cog_embed = discord.Embed(title=f"__Cog:__ {cog.qualified_name}",
					color=ctx.author.color, timestamp=ctx.created_at)
					commands = []
					subcommands = []
					for c in cog.get_commands():
							if not c.hidden:
									commands.append(c.name)
							try:
								for sb in c.commands:
									if not c.hidden:
										subcommands.append(sb.qualified_name)
							except AttributeError:
								pass

					cog_embed.description = f"__**Description:**__\n```{cog.description}```\n`Commands:` {', '.join(commands)}\n\n`Subcommands:` {', '.join(subcommands)}"

					return await ctx.send(embed=cog_embed)

		# Otherwise, it's an invalid parameter (Not found)
		else:
			await ctx.send(f"**Invalid parameter! `{cmd}` is neither a command nor a cog!**")


@slash.slash(name="servers", description="Shows how many servers the bot is in.", guild_ids=TEST_GUILDS)
async def servers(ctx):

	await ctx.send(f"**I'm currently declining in {len(client.guilds)} servers!**", hidden=True)

@client.command(hidden=True)
@commands.is_owner()
async def load(ctx, extension: str):
	'''
	(Owner) loads a cog.
	'''
	if not extension:
		return await ctx.send("**Please, inform an extension!**")
	for cog in os.listdir('./cogs'):
			if str(cog[:-3]).lower() == str(extension).lower():
				try:
					client.load_extension(f"cogs.{cog[:-3]}")
				except commands.ExtensionAlreadyLoaded:
					return await ctx.send(f"**The `{extension}` cog is already loaded!**")
				return await ctx.send(f"**`{extension}` cog loaded!**")
	else:
		await ctx.send(f"**`{extension}` is not a cog!**")


@client.command(hidden=True)
@commands.is_owner()
async def unload(ctx, extension: str):
	'''
	(Owner) unloads a cog.
	'''
	if not extension:
		return await ctx.send("**Please, inform an extension!**")
	for cog in client.cogs:
			if str(cog).lower() == str(extension).lower():
				try:
					client.unload_extension(f"cogs.{cog}")
				except commands.ExtensionNotLoaded:
					return await ctx.send(f"**The `{extension}` cog is not even loaded!**")
				return await ctx.send(f"**`{extension}` cog unloaded!**")
	else:
		await ctx.send(f"**`{extension}` is not a cog!**")


@client.command(hidden=True)
@commands.is_owner()
async def reload(ctx, extension: str):
	'''
	(Owner) reloads a cog.
	'''
	if not extension:
		return await ctx.send("**Please, inform an extension!**")
	
	for cog in client.cogs:
			if str(cog).lower() == str(extension).lower():
				try:
					client.unload_extension(f"cogs.{cog}")
					client.load_extension(f"cogs.{cog}")
				except commands.ExtensionNotLoaded:
					return await ctx.send(f"**The `{extension}` cog is not even loaded!**")
				return await ctx.send(f"**`{extension}` cog reloaded!**")
	else:
		await ctx.send(f"**`{extension}` is not a cog!**")


@client.command(hidden=True)
@commands.is_owner()
async def reload_all(ctx):
	'''
	(Owner) reloads all cogs.
	'''
	for file_name in os.listdir('./cogs'):
		try:
			if str(file_name).endswith(".py"):
				client.unload_extension(f"cogs.{file_name[:-3]}")
				client.load_extension(f"cogs.{file_name[:-3]}")
		except commands.ExtensionNotLoaded:
			pass
	await ctx.send(f"**Cogs reloaded!**")

@slash.slash(name="patreon", description="Support the creator on Patreon.", guild_ids=TEST_GUILDS)
async def patreon(ctx):

	link = 'https://www.patreon.com/dnk'

	embed = discord.Embed(
	title="__Patreon__",
	description=f"If you want to finacially support my work and motivate me to keep adding more features, put more effort and time into this and other bots, click [here]({link})",
	timestamp=ctx.created_at,
	url=link,
	color=ctx.author.color
	)
	await ctx.send(embed=embed, hidden=True)

@slash.slash(name="support", description="Support for the bot and its commands.", guild_ids=TEST_GUILDS)
async def support(ctx):

	link = 'https://discord.gg/languages'

	embed = discord.Embed(
	title="__Support__",
	description=f"For any support; in other words, questions, suggestions or doubts concerning the bot and its commands, contact me **DNK#6725**, or join our support server by clicking [here]({link})",
	timestamp=ctx.created_at,
	url=link,
	color=ctx.author.color
	)
	await ctx.send(embed=embed, hidden=True)



@slash.slash(name="vote", description="Vote for me on TopGG", guild_ids=TEST_GUILDS)
@commands.cooldown(1, 15, commands.BucketType.user)
async def vote(ctx):

	link = 'https://top.gg/bot/753754955005034497/vote'
	embed = discord.Embed(
		title="__Vote__",
		description=f"Click [here]({link}) to vote.",
		url=link,
		color=ctx.author.color
	)
	await ctx.send(embed=embed, hidden=True)


for file_name in os.listdir('./cogs'):
	
	if file_name not in [
		'Declension.py', 'Conjugation.py', 'Dictionaries.py', 'Tools.py', 'ReversoContext.py', 'Songs.py', 'FlashCard.py', 'Expressions.py']: continue
	if str(file_name).endswith(".py"):
		print(file_name)
		client.load_extension(f"cogs.{file_name[:-3]}")
		

client.run(token)