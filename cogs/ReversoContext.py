import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
from discord_slash.model import ButtonStyle
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from datetime import datetime
from cogs.FlashCard import FlashCard
import os
from others import utils

TEST_GUILDS = [792401342969675787]

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


  @cog_ext.cog_subcommand(
		base="context", name="spanish",
		description="Searches and shows examples of X words and sentences in context.", options=[
			create_option(name="search", description="What to search.", option_type=3, required=True)
		], guild_ids=TEST_GUILDS
	)
  async def spanish(self, interaction: SlashContext, search: str) -> None:

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", hidden=True)

    root = 'https://context.reverso.net/translation/spanish-english'

    emoji = "🇪🇸-🇲🇽"
    return await self._reverso(interaction, root, search, 'Spanish', emoji)

  @cog_ext.cog_subcommand(
		base="context", name="italian",
		description="Searches and shows examples of X words and sentences in context.", options=[
			create_option(name="search", description="The word you are looking for.", option_type=3, required=True)
		], guild_ids=TEST_GUILDS
	)
  async def italian(self, interaction: SlashContext, search: str) -> None:

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", hidden=True)

    root = 'https://context.reverso.net/translation/italian-english'

    emoji = "🇮🇹-🇨🇭"
    return await self._reverso(interaction, root, search, 'Italian', emoji)

  @cog_ext.cog_subcommand(
		base="context", name="french",
		description="Searches and shows examples of X words and sentences in context.", options=[
			create_option(name="search", description="The word you are looking for.", option_type=3, required=True)
		], guild_ids=TEST_GUILDS
	)
  async def french(self, interaction: SlashContext, search: str) -> None:

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", hidden=True)

    root = 'https://context.reverso.net/translation/french-english'

    emoji = "🇫🇷-🇧🇪"
    return await self._reverso(interaction, root, search, 'French', emoji)

  @cog_ext.cog_subcommand(
		base="context", name="german",
		description="Searches and shows examples of X words and sentences in context.", options=[
			create_option(name="search", description="The word you are looking for.", option_type=3, required=True)
		], guild_ids=TEST_GUILDS
	)
  async def german(self, interaction: SlashContext, search: str) -> None:

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", hidden=True)

    root = 'https://context.reverso.net/translation/german-english'

    emoji = "🇩🇪-🇦🇹"
    return await self._reverso(interaction, root, search, 'German', emoji)

  @cog_ext.cog_subcommand(
		base="context", name="polish",
		description="Searches and shows examples of X words and sentences in context.", options=[
			create_option(name="search", description="The word you are looking for.", option_type=3, required=True)
		], guild_ids=TEST_GUILDS
	)
  async def polish(self, interaction: SlashContext, search: str) -> None:

    if len(search) > 100:
      return await interaction.send("**Wow! Your search must be within 100 characters!**", hidden=True)

    root = 'https://context.reverso.net/translation/polish-english'

    emoji = "🇵🇱"
    return await self._reverso(interaction, root, search, 'Polish', emoji)

  async def _reverso(self, interaction: SlashContext, root: str, search: str, language: str, emoji: str) -> None:
    """ Gets context in ReversoContext's website for some languages.
    :param root: The root endpoint to perform the GET HTTP request.
    :param search: What is going to be searched.
    :param language: The language that it's being searched for."""

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
      
      index = 0
      # Initial embed
      embed = discord.Embed(
        description=f"**Searched query:** {search}\n**Search Translations:** {', '.join(translations)}",
        color=interaction.author.color,
        timestamp=interaction.created_at,
        url=req

      )

      await interaction.defer(hidden=True)

      button_ctx = None

      action_row = create_actionrow(
					create_button(
							style=ButtonStyle.blurple, label="Previous", custom_id="left_btn", emoji='⬅️'
					),
					create_button(
							style=ButtonStyle.blurple, label="Next", custom_id="right_btn", emoji='➡️'
					),
					create_button(
							style=ButtonStyle.green, label="Add Card", custom_id="add_btn", emoji='➕'
					),
					create_button(
							style=ButtonStyle.red, label="Stop", custom_id="stop_btn", emoji='🛑'
					)
			)

      # Main loop, for switching pages
      while True:
        # if button_ctx:
        #   await button_ctx.defer(edit_origin=True)

        print(embed)

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
        if button_ctx is None:
          await interaction.send(embed=embed, components=[action_row], hidden=True)
          # Wait for someone to click on them
          button_ctx = await wait_for_component(self.client, components=action_row)
        else:
          await button_ctx.edit_origin(embed=embed, components=[action_row])
          # Wait for someone to click on them
          button_ctx = await wait_for_component(self.client, components=action_row, messages=button_ctx.origin_message_id)

        # Waits for user reaction to switch pages
        if button_ctx.custom_id == 'left_btn':
          await button_ctx.defer(edit_origin=True)
          if index > 0:
            index -= 1
          continue
        elif button_ctx.custom_id == 'right_btn':
          print('ici?')
          await button_ctx.defer(edit_origin=True)
          print('oui, bien là au-dessus !')
          if index < len(groups) - 1:
            index += 1
          continue
        elif button_ctx.custom_id == 'add_btn':
          await button_ctx.defer(edit_origin=True)
          front = groups[index]['original']
          back = groups[index]['translation']
          await self._add_card(interaction, interaction.author, front, back)
          continue
        elif button_ctx.custom_id == 'stop_btn':
          await button_ctx.defer(edit_origin=True)
          
          for button in action_row['components']:
            button['disabled'] = True

          return await button_ctx.edit_origin(embed=embed, components=[action_row])

  async def _add_card(self, interaction: SlashContext, member: discord.Member, front: str, back: str) -> None:
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
        await interaction.reply(f"**Added card into the DB, {member.mention}!**", hidden=True)
      else: 
        await interaction.reply("**This server is not whitelisted!**", hidden=True)
    except Exception as e:
      await interaction.reply(f"**For some reason I couldn't add it into the DB, {member.mention}!**", hidden=True)

def setup(client) -> None:
  """ Cog's setup function."""
  
  client.add_cog(ReversoContext(client))