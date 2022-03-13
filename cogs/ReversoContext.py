import discord
from discord.ext import commands
from discord import ApplicationContext, SlashCommandGroup, Option
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup

import os
from others import utils
from others.views import ReversoContextView
from typing import Union, Any, List, Dict

TEST_GUILDS = [777886754761605140]

class ReversoContext(commands.Cog):
  """ A category regarding the acquisition of words in context for different languages. """

  def __init__(self, client) -> None:
    """ Class initializing method."""

    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)

  _context = SlashCommandGroup('context', 'Searches and shows a word in context in a given language', guild_ids=TEST_GUILDS)

  @commands.Cog.listener()
  async def on_ready(self) -> None:
    """ Tells when the cog is ready to use."""

    print('ReversoContext cog is online!')


  @_context.command(name="spanish")
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def _context_spanish(self, interaction: ApplicationContext, 
    search: Option(str, name="search", description="What to search.", required=True)) -> None:
    """ Searches and shows examples of X words and sentences in context. """

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", ephemeral=True)

    root = 'https://context.reverso.net/translation/spanish-english'

    emoji = "🇪🇸-🇲🇽"
    return await self._reverso(interaction, root, search, 'Spanish', emoji)

  @_context.command(name="italian")
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def _context_italian(self, interaction: ApplicationContext, 
    search: Option(str, name="search", description="The word you are looking for.", required=True)) -> None:
    """ Searches and shows examples of X words and sentences in context. """

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", ephemeral=True)

    root = 'https://context.reverso.net/translation/italian-english'

    emoji = "🇮🇹-🇨🇭"
    return await self._reverso(interaction, root, search, 'Italian', emoji)

  @_context.command(name="french")
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def _context_french(self, interaction: ApplicationContext, 
    search: Option(str, name="search", description="The word you are looking for.", required=True)) -> None:
    """ Searches and shows examples of X words and sentences in context. """

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", ephemeral=True)

    root = 'https://context.reverso.net/translation/french-english'

    emoji = "🇫🇷-🇧🇪"
    return await self._reverso(interaction, root, search, 'French', emoji)

  @_context.command(name="german")
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def _context_german(self, interaction: ApplicationContext, 
    search: Option(str, name="search", description="The word you are looking for.", required=True)) -> None:
    """ Searches and shows examples of X words and sentences in context. """

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", ephemeral=True)

    root = 'https://context.reverso.net/translation/german-english'

    emoji = "🇩🇪-🇦🇹"
    return await self._reverso(interaction, root, search, 'German', emoji)

  @_context.command(name="polish")
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def _context_polish(self, interaction: ApplicationContext, 
    search: Option(str, name="search", description="The word you are looking for.", required=True)) -> None:
    """ Searches and shows examples of X words and sentences in context. """

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", ephemeral=True)

    root = 'https://context.reverso.net/translation/polish-english'

    emoji = "🇵🇱"
    return await self._reverso(interaction, root, search, 'Polish', emoji)

  async def _reverso(self, interaction: ApplicationContext, root: str, search: str, language: str, emoji: str) -> None:
    """ Gets context in ReversoContext's website for some languages.
    :param root: The root endpoint to perform the GET HTTP request.
    :param search: What is going to be searched.
    :param language: The language that it's being searched for."""

    await interaction.defer(ephemeral=True)
    req = f"{root}/{search.replace(' ', '%20')}"

    async with self.session.get(req, headers={'User-Agent': 'Mozilla/5.0'}) as response:
      if not response.status == 200:
        return await interaction.send("**Something went wrong with that search!**")

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
      
      # Additional data:
      additional = {
        'client': self.client,
        'cog': self,
        'emoji': emoji,
        'search': search,
        'title': language,
        'translations': translations,
        'change_embed': self.make_context_embed
      }
      view = ReversoContextView(groups, **additional)
      embed = await view.make_embed(interaction.author)
      await interaction.respond(embed=embed, view=view)

  async def make_context_embed(self, req, emoji: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
    offset: int, lentries: int, entries: Dict[str, Any], title: str, translations: List[str]) -> discord.Embed:
      """ Makes an embed for the current search example.
      :param emoji: The emoji for the language.
      :param member: The member who triggered the command.
      :param search: The search that was performed.
      :param example: The current search example.
      :param offset: The current page of the total entries.
      :param lentries: The length of entries for the given search.
      :param entries: The entries of that search.
      :param title: The title of the search.
      :param translations: The list of translations of the searched word. """

      current_time = await utils.get_time_now()

      # Makes the embed's header
      embed = discord.Embed(
        title=f"{emoji} {title} Context - ({offset}/{lentries})",
        description=f"**Searched query:** {search}\n**Search Translations:** {', '.join(translations)}",
        color=member.color,
        timestamp=current_time,
        url=req
      )

      embed.add_field(
        name=f"Original",
        value=f"```{entries[offset]['original']}```",
        inline=False
      )
      embed.add_field(
        name=f"Translation",
        value=f"```{entries[offset]['translation']}```",
        inline=False
      )

      # Sets the author of the search
      embed.set_author(name=member, icon_url=member.display_avatar)
      # Makes a footer with the a current page and total page counter
      embed.set_footer(text=f"Requested by: {member}", icon_url=member.guild.icon.url)

      return embed
        
  async def _add_card(self, interaction: ApplicationContext, member: discord.Member, front: str, back: str) -> None:
    """" Adds a card from the context list into the DB. 
    :param interaction: The context.
    :param member: The member to whom the card is gonna be added.
    :param front: The value for the frontside of the card.
    :param back: The values for the backside of the card. """

    try:
      the_time = await utils.get_timestamp()
      flashcard = self.client.get_cog('FlashCard')
      inserted = await flashcard._insert_card(interaction.guild_id, member.id, front, back, the_time)

      if inserted:
        await interaction.reply(f"**Added card into the DB, {member.mention}!**", ephemeral=True)
      else: 
        await interaction.reply("**This server is not whitelisted!**", ephemeral=True)
    except Exception as e:
      await interaction.reply(f"**For some reason I couldn't add it into the DB, {member.mention}!**", ephemeral=True)

def setup(client) -> None:
  """ Cog's setup function."""
  
  client.add_cog(ReversoContext(client))