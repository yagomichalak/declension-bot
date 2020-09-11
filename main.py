import discord
from discord.ext import commands, tasks
import os
import asyncio
from re import match

client = commands.Bot(command_prefix='!')
token = os.getenv('TOKEN')

@client.event
async def on_ready():
  print("Bot is ready!")


@client.event
async def on_command_error(ctx, error):
  
  if isinstance(error, commands.CommandOnCooldown):
      await ctx.send(error)

  print(error)

@client.event
async def on_message(message):
  if message.author.bot:
    return
  if match(f"<@!?{client.user.id}>", message.content) is not None:
    await message.channel.send(f"**{message.author.mention}, my prefix is `{client.command_prefix}`**")

  await client.process_commands(message)


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

for filename in os.listdir('./cogs'):
  if filename.endswith('.py'):
    client.load_extension(f"cogs.{filename[:-3]}")

client.run(token)