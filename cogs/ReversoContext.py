import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from datetime import datetime
from cogs.FlashCard import FlashCard

class ReversoContext(commands.Cog):
  """ A category regarding the acquisition of words in context for different languages. """

  def __init__(self, client) -> None:
    """ Class initializing method."""

    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)


  @commands.Cog.listener()
  async def on_ready(self) -> None:
    """ Tells when the cog is ready to use."""

    print('ReversoContext cog is online!')

  
  @commands.group(aliases=['ctx'])
  async def context(self, ctx) -> None:
    """ Gets context in ReversoContext's website for some languages. """

    if ctx.invoked_subcommand:
      return
    
    cmd = self.client.get_command('context')
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

  @context.command(aliases=['es'])
  async def spanish(self, ctx, *, search: str = None) -> None:
    """ Searches and shows examples of Spanish words and sentences in context.
    :param search: What you want to be searched.```
    **🇪🇸-🇲🇽 Example:**
    ```ini
    [1] dec!ctx es perro
    [2] dec!ctx spanish el pollo
    [3] dec!context spanish mujer"""

    if not search:
      return await ctx.send("**Inform a query to search for context!**")

    if len(search) > 100:
      return await ctx.send("**Wow! Your searched must be within 100 characters!**")

    root = 'https://context.reverso.net/translation/spanish-english'

    emoji = "🇪🇸-🇲🇽"
    return await self._reverso(ctx, root, search, 'Spanish', emoji)

  @context.command(aliases=['it'])
  async def italian(self, ctx, *, search: str = None) -> None:
    """ Searches and shows examples of Italian words and sentences in context.
    :param search: What you want to be searched.```
    **🇮🇹-🇨🇭 Example:**
    ```ini
    [1] dec!ctx it ragazzo
    [2] dec!ctx italian tempo
    [3] dec!context italian piccolo"""

    if not search:
      return await ctx.send("**Inform a query to search for context!**")

    if len(search) > 100:
      return await ctx.send("**Wow! Your searched must be within 100 characters!**")

    root = 'https://context.reverso.net/translation/italian-english'

    emoji = "🇮🇹-🇨🇭"
    return await self._reverso(ctx, root, search, 'Italian', emoji)

  @context.command(aliases=['fr'])
  async def french(self, ctx, *, search: str = None) -> None:
    """ Searches and shows examples of French words and sentences in context.
    :param search: What you want to be searched.```
    **🇫🇷-🇧🇪 Example:**
    ```ini
    [1] dec!ctx fr pain
    [2] dec!ctx french saouler
    [3] dec!context french chaise"""

    if not search:
      return await ctx.send("**Inform a query to search for context!**")

    if len(search) > 100:
      return await ctx.send("**Wow! Your searched must be within 100 characters!**")

    root = 'https://context.reverso.net/translation/french-english'

    emoji = "🇫🇷-🇧🇪"
    return await self._reverso(ctx, root, search, 'French', emoji)

  @context.command(aliases=['de'])
  async def german(self, ctx, *, search: str = None) -> None:
    """ Searches and shows examples of German words and sentences in context.
    :param search: What you want to be searched.```
    **🇩🇪-🇦🇹 Example:**
    ```ini
    [1] dec!ctx de groß
    [2] dec!ctx german zeit
    [3] dec!context german Luft"""

    if not search:
      return await ctx.send("**Inform a query to search for context!**")

    if len(search) > 100:
      return await ctx.send("**Wow! Your searched must be within 100 characters!**")

    root = 'https://context.reverso.net/translation/german-english'

    emoji = "🇩🇪-🇦🇹"
    return await self._reverso(ctx, root, search, 'German', emoji)

  async def _reverso(self, ctx, root: str, search: str, language: str, emoji: str) -> None:
    """ Gets context in ReversoContext's website for some languages.
    :param root: The root endpoint to perform the GET HTTP request.
    :param search: What is going to be searched.
    :param language: The language that it's being searched for."""

    req = f"{root}/{search.replace(' ', '%20')}"

    async with self.session.get(req, headers={'User-Agent': 'Mozilla/5.0'}) as response:
      if not response.status == 200:
        return await ctx.send("**Something went wrong with that search!**")

      html = BeautifulSoup(await response.read(), 'html.parser')
      

      # Gets  all examples
      examples = html.select('#examples-content > div')
      groups = []

      # Strips and formats the content text for each example
      for ex in examples:
        original = ex.select_one('div.src.ltr')
        translation = ex.select_one('div.trg.ltr')
        if not original and not translation:
          continue

        original = original.get_text().strip()
        translation = translation.get_text().strip()
        groups.append({'original': original, 'translation': translation})

      
      # Gets all translations
      translations = [tr.get_text().strip() for tr in html.select('#translations-content > a') if tr.get_text()]
      
      index = 0
      # Initial embed
      embed = discord.Embed(
        description=f"**Searched query:** {search}\n**Search Translations:** {', '.join(translations)}",
        color=ctx.author.color,
        timestamp=ctx.message.created_at,
        url=req

      )
      msg = await ctx.send(embed=discord.Embed(title="**Getting context...**"))
      await asyncio.sleep(0.5)
      await msg.add_reaction('⬅️')
      await msg.add_reaction('➡️')
      await msg.add_reaction('➕')
      await msg.add_reaction('🛑')

      # Main loop, for switching pages
      while True:
        embed.title = f"{emoji} {language} Context - ({index+1}/{len(groups)})"
        embed.clear_fields()
        embed.add_field(
          name=f"Original",
          value=f"```{groups[index]['original']}```",
          inline=False
        )
        embed.add_field(
          name=f"Translation",
          value=f"```{groups[index]['translation']}```",
          inline=False
        )
        # Sends to Discord the current state of the embed
        await msg.edit(embed=embed)

        # Waits for user reaction to switch pages
        try:
          r, u = await self.client.wait_for(
            'reaction_add', timeout=60, 
            check=lambda r, u: r.message.id == msg.id and \
            u.id == ctx.author.id and str(r.emoji) in ['⬅️', '➡️', '➕', '🛑']
          )
        except asyncio.TimeoutError:
          await msg.remove_reaction('⬅️', self.client.user)
          await msg.remove_reaction('➡️', self.client.user)
          await msg.remove_reaction('➕', self.client.user)
          await msg.remove_reaction('🛑', self.client.user)
          return
        else:
          if str(r.emoji) == '⬅️':
            if index > 0:
              index -= 1
            await msg.remove_reaction(r, u)
            continue
          elif str(r.emoji) == '➡️':
            if index < len(groups) - 1:
              index += 1
            await msg.remove_reaction(r, u)
            continue
          elif str(r.emoji) == '➕':
            front = groups[index]['original']
            back = groups[index]['translation']
            await self._add_card(ctx, ctx.author, front, back)
            await msg.remove_reaction(r, u)
            continue
          elif str(r.emoji) == '🛑':
            await msg.remove_reaction('⬅️', self.client.user)
            await msg.remove_reaction('➡️', self.client.user)
            await msg.remove_reaction('➕', self.client.user)
            await msg.remove_reaction('🛑', self.client.user)
            await msg.remove_reaction('🛑', ctx.author)
            break

  async def _add_card(self, ctx, member: discord.Member, front: str, back: str) -> None:
    """" Adds a card from the context list into the DB. 
    :param ctx: The context.
    :param member: The member to whom the card is gonna be added.
    :param front: The value for the frontside of the card.
    :param back: The values for the backside of the card. """

    try:
      epoch = datetime.utcfromtimestamp(0)
      the_time = (datetime.utcnow() - epoch).total_seconds()
      flashcard = FlashCard(self.client)
      await flashcard._insert_card(member.id, front, back, the_time)
      return await ctx.send(f"**Added card into the DB, {member.mention}!**", delete_after=3)
    except Exception as e:
      return await ctx.send(f"**For some reason I couldn't add it into the DB, {member.mention}!**", delete_after=3)

def setup(client) -> None:
  """ Cog's setup function."""
  
  client.add_cog(ReversoContext(client))