import discord
from discord.ext import commands, tasks
import os
from random import randint
from re import match
from itertools import cycle
from others import utils
from others.customerrors import NotInWhitelist
from dotenv import load_dotenv
load_dotenv()

IS_LOCAL = utils.is_local()
TEST_GUILDS = [os.getenv("TEST_GUILD_ID")] if IS_LOCAL else None

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

client = commands.Bot(command_prefix='dec!', intents=discord.Intents.default(), help_command=None)
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
async def on_application_command_error(ctx, error) -> None:

    if isinstance(error, commands.CommandOnCooldown):
        secs = int(float(error.retry_after))
        await ctx.respond(content=f"You are on cooldown! Try again in {secs} seconds!", ephemeral=True)

    else:
        print(error)


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if match(f"<@!?{client.user.id}>", message.content) is not None:
        await message.channel.send(f"**{message.author.mention}, my prefix is `/`**")

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

    # Logs it in the bot's support server on_guild log
    guild_log = client.get_channel(int(on_guild_log_id))
    if guild_log:
        embed.set_thumbnail(url=guild.icon.url)
        await guild_log.send(embed=embed)


@client.event
async def on_guild_remove(guild):
    embed = discord.Embed(
        title="Goodbye world!",
        description=f"Our server number {len(client.guilds)+1}, called **{guild.name}**, gave up on declining languages... LOL!",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=guild.icon.url)
    # Logs it in the bot's support server's on_guild log
    guild_log = client.get_channel(int(on_guild_log_id))
    if guild_log:
        await guild_log.send(embed=embed)


@client.slash_command(name="ping", guild_ids=TEST_GUILDS)
async def ping(ctx):
    """ Shows the bot's latency. """

    await ctx.respond(f"**Ping: __{round(client.latency * 1000)}__ ms**", ephemeral=True)


@client.slash_command(name="info", guild_ids=TEST_GUILDS)
@commands.cooldown(1, 10, type=commands.BucketType.guild)
async def info(ctx):
    """  "Shows some information about the bot itself. """

    current_time = await utils.get_time_now()
    embed = discord.Embed(
        title='Declinator Bot', description=" **WHAT IS IT?**```Hello, the Declinator bot is an open source bot for word declension, verb conjugation and words in context.\nPS: Declension is the changing of the form of a word in function of its grammatical case.```",
        colour=ctx.author.color, url="https://languagesloth.com/bots/", timestamp=current_time)
    embed.add_field(name="📚 **Language declinators**",
                                value="So far, there are `4` different languages to decline, `34` to conjugate and `4` to get word-in-context.",
                                inline=True)
    embed.add_field(name="💻 **Programmed in**",
                                value="The Declinator bot was built in Python, and you can find its GitHub repository [here](https://github.com/yagomichalak/declension-bot).",
                                inline=True)
    embed.add_field(name='❓ **How do you do It?**',
                                value="The bot either web scrapes or uses an API to fetch data from websites, and after that, the bot does its magic to show that data nicely in an embedded message.",
                                inline=True)
    embed.add_field(name="🌎 **More languages** ",
                                value="More languages will be added as I'm requested and have some time to implement them.", inline=True)
    embed.set_footer(text=ctx.guild.name,
                                icon_url='https://cdn.discordapp.com/icons/459195345419763713/a_dff4456b872c84146a78be8422e33cc2.gif?size=1024')
    embed.set_thumbnail(
        url=client.user.display_avatar)
    embed.set_author(name='dnkofficial', url='https://discord.gg/languages',
                                icon_url='https://languagesloth.com/static/assets/images/misc/dnk-pfp.png')

    view: discord.ui.View = discord.ui.View()
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Terms of Service", emoji='🤝', url="https://languagesloth.com/bots/declinator/terms-of-service"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Privacy & Policy", emoji='🕵️', url="https://languagesloth.com/bots/declinator/privacy-policy"))

    await ctx.respond(embed=embed, view=view, ephemeral=True)


@client.slash_command(name="invite", guild_ids=TEST_GUILDS)
async def invite(ctx):
    """ Sends the bot's invite. """

    invite = 'https://discord.com/api/oauth2/authorize?client_id=753754955005034497&permissions=105226750976&scope=bot%20applications.commands'
    await ctx.respond(f"Here's my invite:\n{invite}", ephemeral=True)


@client.slash_command(name="servers", guild_ids=TEST_GUILDS)
async def servers(ctx):
    """ Shows how many servers the bot is in. """

    await ctx.respond(f"**I'm currently declining in {len(client.guilds)} servers!**", ephemeral=True)


@client.command(ephemeral=True)
@commands.is_owner()
async def load(ctx, extension: str):
    """ (Owner) loads a cog. """

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


@client.command(ephemeral=True)
@commands.is_owner()
async def unload(ctx, extension: str):
    """ (Owner) unloads a cog. """

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


@client.command(ephemeral=True)
@commands.is_owner()
async def reload(ctx, extension: str):
    """ (Owner) reloads a cog. """

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


@client.command(ephemeral=True)
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
    await ctx.send("**Cogs reloaded!**")


@client.slash_command(name="patreon", guild_ids=TEST_GUILDS)
async def patreon(ctx):
    """ Support the creator on Patreon. """

    await ctx.defer(ephemeral=True)
    link = 'https://www.patreon.com/dnk'

    current_time = await utils.get_time_now()
    embed = discord.Embed(
        title="__Patreon__",
        description=f"If you want to finacially support my work and motivate me to keep adding more features, put more effort and time into this and other bots, click [here]({link})",
        timestamp=current_time,
        url=link,
        color=ctx.author.color
    )
    await ctx.respond(embed=embed, ephemeral=True)


@client.slash_command(name="support", guild_ids=TEST_GUILDS)
async def support(ctx):
    """ Support for the bot and its commands. """

    await ctx.defer(ephemeral=True)
    link = 'https://discord.gg/languages'

    current_time = await utils.get_time_now()
    embed = discord.Embed(
        title="__Support__",
        description=f"For any support; in other words, questions, suggestions or doubts concerning the bot and its commands, contact me **DNK#6725**, or join our support server by clicking [here]({link})",
        timestamp=current_time,
        url=link,
        color=ctx.author.color
    )
    await ctx.respond(embed=embed, ephemeral=True)


@client.slash_command(name="vote", guild_ids=TEST_GUILDS)
@commands.cooldown(1, 15, commands.BucketType.user)
async def vote(ctx):
    """ Vote for me on TopGG """

    await ctx.defer(ephemeral=True)
    widget = f'https://top.gg/api/widget/753754955005034497.png?{randint(0, 2147483647)}topcolor=2C2F33&middlecolor=23272A&usernamecolor=FFFFF0&certifiedcolor=FFFFFF&datacolor=F0F0F0&labelcolor=99AAB5&highlightcolor=2C2F33'

    link = 'https://top.gg/bot/753754955005034497/vote'
    embed = discord.Embed(
        title="__Vote__",
        description=f"Click [here]({link}) to vote.",
        url=link,
        color=ctx.author.color
    )
    embed.set_thumbnail(url=client.user.display_avatar)
    embed.set_image(url=widget)

    view: discord.ui.View = discord.ui.View()
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Previous", emoji='🆙', url=link))

    await ctx.respond(embed=embed, view=view, ephemeral=True)


for file_name in os.listdir('./cogs'):

    if file_name in []:
        continue
    if str(file_name).endswith(".py"):
        print(file_name)
        client.load_extension(f"cogs.{file_name[:-3]}")

if __name__ == "__main__":

    token = os.getenv("DEV_TOKEN") if IS_LOCAL else os.getenv("PROD_TOKEN")
    client.run(token)
