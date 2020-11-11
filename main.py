import discord
from discord.ext import commands, tasks
import os
import asyncio
from re import match
from itertools import cycle

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
  "Vietnamese conjugations"
  ])

intents = discord.Intents.default()
client = commands.Bot(command_prefix='dec!', intents=intents)
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

  if isinstance(error, commands.MissingPermissions):
    await ctx.send(error)

  if isinstance(error, commands.BotMissingPermissions):
    await ctx.send("**I don't have permissions to run this command!**")

  if isinstance(error, commands.BadArgument):
    await ctx.send("**Invalid parameters!**")

  if isinstance(error, commands.CommandOnCooldown):
    secs = error.retry_after
    if int(secs) >= 60:
      await ctx.send(f"You are on cooldown! Try again in {secs/60:.1f} minutes!")
    else:
      await ctx.send(error)
      
  if isinstance(error, commands.NotOwner):
    await ctx.send("**You can't do that, you're not the owner!**")

  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send('**Make sure to inform all parameters!**')

  print(error)


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

@client.command()
async def ping(ctx):
  '''
  Shows the latency.
  '''
  await ctx.send(f"**Ping: __{round(client.latency * 1000)}__ ms**")


@client.command()
@commands.cooldown(1, 10, type=commands.BucketType.guild)
async def info(ctx):
  '''
  Shows some information about the bot itself.
  '''
  embed = discord.Embed(title='Declinator Bot', description="__**WHAT IS IT?:**__```Hello, the Declinator bot is an open source bot based on word declensions and verb conjugations.\nPS: declensions are all forms of a word in a language that contains a grammatical case system.```", colour=ctx.author.color, url="http://193.70.127.179/", timestamp=ctx.message.created_at)
  embed.add_field(name="📚 __**Language declinators**__",
                value="`4` different languages to decline and `23` to conjugate so far.",
                inline=True)
  embed.add_field(name="💻 __**Programmed in**__",
                value="The Declinator bot was built in Python, and you can find its GitHub repository [here](https://github.com/yagomichalak/declension-bot).",
                inline=True)
  embed.add_field(name='❓ __**How do you do It?**__',
                value="The bot either web scrapes or use an API to fetch information from websites, after that, the bot does its magic to nicely show the information in an embedded message.",
                inline=True)
  embed.add_field(name="🌎 __**More languages**__ ", 
                value="More languages will be added as I'm requested and have some time to implement them.", inline=True)
  embed.set_footer(text=ctx.guild.name,
                icon_url='https://cdn.discordapp.com/icons/459195345419763713/a_dff4456b872c84146a78be8422e33cc2.gif?size=1024')
  embed.set_thumbnail(
    url=client.user.avatar_url)
  embed.set_author(name='DNK#6725', url='https://discord.gg/languages',
                icon_url='https://cdn.discordapp.com/attachments/719020754858934294/720289112040669284/DNK_icon.png')
  await ctx.send(embed=embed)

@client.command()
async def invite(ctx):
  '''
  Sends the bot's invite.
  '''
  invite = 'https://discord.com/api/oauth2/authorize?client_id=753754955005034497&permissions=59456&scope=bot'
  await ctx.send(f"Here's my invite:\n{invite}")

@client.command()
async def help(ctx, *, cmd: str = None):
  '''
  Shows some information about commands and categories.
  '''
  if not cmd:
      embed = discord.Embed(
      title="All commands and categories",
      description=f"```ini\nUse {client.command_prefix}help command or {client.command_prefix}help category to know more about a specific command or category\n\n[Examples]\n[1] Category: {client.command_prefix}help Declension\n[2] Command : {client.command_prefix}help german```",
      timestamp=ctx.message.created_at,
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
      command_embed = discord.Embed(title=f"__Command:__ {command.name}", description=f"__**Description:**__\n```{command.help}```", color=ctx.author.color, timestamp=ctx.message.created_at)
      return await ctx.send(embed=command_embed)

    for cog in client.cogs:
      if str(cog).lower() == str(cmd).lower():
          cog = client.get_cog(cog)
          cog_embed = discord.Embed(title=f"__Cog:__ {cog.qualified_name}",
          color=ctx.author.color, timestamp=ctx.message.created_at)
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


@client.command()
async def servers(ctx):
  '''
  Shows how many servers the bot is in.
  '''
  await ctx.send(f"**I'm currently declining in {len(client.guilds)} servers!**")

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

@client.command()
async def support(ctx):
  '''
  Support for the bot and its commands.
  '''
  link = 'https://discord.gg/languages'

  embed = discord.Embed(
  title="__Support__",
  description=f"For any support; in other words, questions, suggestions or doubts concerning the bot and its commands, contact me **DNK#6725**, or join our support server by clicking [here]({link})",
  timestamp=ctx.message.created_at,
  url=link,
  color=ctx.author.color
  )
  await ctx.send(embed=embed)

@client.command()
async def vote(ctx):
  '''
  Vote for me on TopGG!
  '''
  link = 'https://top.gg/bot/753754955005034497/vote'
  embed = discord.Embed(
    title="__Vote__",
    description=f"Click [here]({link}) to vote.",
    url=link,
    color=ctx.author.color
  )
  await ctx.send(embed=embed)


for file_name in os.listdir('./cogs'):
  if str(file_name).endswith(".py"):
    client.load_extension(f"cogs.{file_name[:-3]}")
    

client.run(token)