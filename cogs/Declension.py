import discord
from discord.ext import commands
from discord import slash_command, option, Option, OptionChoice, SlashCommandGroup

import aiohttp
import os
from os import getenv
from datetime import datetime

import convertapi
from PIL import Image
import time
from bs4 import BeautifulSoup
import copy
from itertools import zip_longest

from others import utils
from others.views import PaginatorView
from typing import Dict, Union, Any
from pprint import pprint

IS_LOCAL = utils.is_local()
TEST_GUILDS = [os.getenv("TEST_GUILD_ID")] if IS_LOCAL else None


class Declension(commands.Cog):
  '''
  A category for word declensions.
  '''

  def __init__(self, client):
    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)
    self.pdf_token = getenv('PDF_API_TOKEN')

  _decline = SlashCommandGroup("decline", "Declines a word in a given language", guild_ids=TEST_GUILDS)

  @commands.Cog.listener()
  async def on_ready(self):
    print('Declension cog is online!')

  @_decline.command(name='polish')
  @commands.cooldown(1, 15, commands.BucketType.user)
  @utils.check_command_limit()
  async def _decline_polish(self, ctx, word: Option(str, name='word', description='The word to decline', required=True)):

    await ctx.defer(ephemeral=True)
    word = word.replace(" ", "")
    current_time = await utils.get_time_now()

    root = "https://www.api.declinator.com/api/v2/declinator"
    req = f"{root}/pl?unit={word}"
    headers = {"Authorization": os.getenv("DECLINATOR_API_TOKEN")}

    async with self.session.get(req, headers=headers) as response:
      if response.status != 200:
        return await ctx.respond("**For some reason I couldn't process it!**", ephemeral=True)

      data = (await response.json())[0]

      gender_text = "" if not (gender := data.get("gender", "")) else f"| **Gender:** {gender}"

      # Creates the embed
      embed = discord.Embed(
        title="Polish Declension",
        description=f"**Search:** {word.lower()} | **Word**: {data['singular']['n'].lower()} {gender_text}".strip(),
        color=ctx.author.color,
        url=req,
        timestamp=current_time
      )

      # Removes the gender key from the data
      if "gender" in data:
        del data["gender"]

      case_names_mapping = {
        "n": "nominative",
        "g": "genitive",
        "d": "dative",
        "a": "accusative",
        "i": "instrumental",
        "l": "locative",
        "v": "vocative"
      }

      # Loops through the word modes and get equivalent cases and values
      for grammatical_number, cases in data.items():
        temp_text = ""
        for case, declension in cases.items():
          case_name = case_names_mapping.get(case.lower(), case)
          line = f"{case_name.title():<12}| {declension.title()}\n"
          temp_text += line

        # Appends a field for each grammatical number, containing also the cases and their respective declined words
        embed.add_field(
          name=grammatical_number.title(),
          value=f"```apache\n{temp_text}```",
          inline=True)

      await ctx.respond(embed=embed, ephemeral=True)


  async def _outdated_decline_polish(self, ctx, word: str = None):

    await ctx.defer(ephemeral=True)

    me = ctx.author
    if not word:
      return await ctx.respond(f"**Please {me.mention}, inform a word to search!**", ephemeral=True)

    root = 'http://online-polish-dictionary.com/word'

    async with self.session.get(f"{root}/{word}") as response:
      if response.status != 200:
        return await ctx.respond("**For some reason I couldn't process it!**", ephemeral=True)

      data = await response.text()

      start = 'https://e-polish.eu/dictionary/en/'
      end = '.pdf'
      s = data.find(start)
      e = data.find(end)
      url = data[s:e+4]

    async with self.session.get(url) as response:
      if response.status != 200:
        return await ctx.response("**For some reason I couldn't process it!**", ephemeral=True)

      try:
        with open(f'files/{me.id}.pdf', 'wb') as f:
          f.write(await response.read())
      except Exception:
        return await ctx.response("**I couldn't find anything for that word!**", ephemeral=True)
    
    convertapi.api_secret = self.pdf_token
    convertapi.convert('png', {
    'File': f'./files/{me.id}.pdf',  
}, from_format = 'pdf').save_files('./files')

    # Opens a image in RGB mode 
    im = Image.open(rf"files/{me.id}.png") 
      
    # Size of the image in pixels (size of orginal image) 
    # (This is not mandatory) 
      
    # Setting the points for cropped image 
    left = 155
    top = 300
    right = 1550
    bottom = 1550
      
    # Cropped image of above dimension 
    # (It will not change orginal image) 
    im1 = im.crop((left, top, right, bottom))  
        
    # Shows the image in image viewer 
    im1.save(f'files/{me.id}.png')

    file = discord.File(f'files/{me.id}.png', filename='polish.png')
    await ctx.respond(file=file)
    os.remove(f"files/{me.id}.pdf")
    os.remove(f"files/{me.id}.png")
  
  @_decline.command(name='russian', options=[
      Option(str, name='word', description='The word to decline', required=True)
    ]
  )
  @commands.cooldown(1, 10, commands.BucketType.user)
  @utils.check_command_limit()
  async def _decline_russian(self, ctx, word: str = None):
    """ Declines a Russian word; showing a table with its full declension forms. """
    await ctx.defer()

    if not word:
      return await ctx.send("**Please, type a word**", ephemeral=True)

    current_time = await utils.get_time_now()
    root = 'https://en.openrussian.org/ru'

    req = f"{root}/{word.lower()}"
    async with self.session.get(req) as response:
      if response.status != 200:
        return await ctx.respond("**Something went wrong with that search!**", ephemeral=True)
    
      # Gets the html and the table div
      html = BeautifulSoup(await response.read(), 'html.parser')
      div = html.select_one('.table-container')

      if not div:
        return await ctx.respond("**I couldn't find anything for this!**", ephemeral=True)

      # Gets the word modes (singular, plura, m., f., etc)
      word_modes = []
      for mode in div.select('.table-audio'):
        # Checks whether the row has a long version of the mode
        if value := mode.select_one('.long'):
          if value.text:
            word_modes.append(value.text.strip())
        # If not just tries to get its content
        else:
          if mode.text:
            word_modes.append(mode.text.strip())

      if not word_modes:
        return await ctx.respond("**I can't decline this word, maybe this is a verb!**", ephemeral=True)
      # Gets all case names
      case_names = [case.text.strip() for case in div.select('tbody tr th .short') if case.text]
      if not case_names:
        return await ctx.respond("**No cases found for this word, maybe this is a verb!**", ephemeral=True)

      # Gets all values
      case_values = []
      for case in div.select('tbody tr'):
        row_values = []
        for row in case.select('td'):
          if value := row.get_text(" | ", strip=True):
            row_values.append(value.strip())

        case_values.append(row_values)

      tds = [td for td in div.select('tbody tr')]
      # Makes the embedded message
      embed = discord.Embed(
        title="Russian Declension",
        description=f"**Word:** {word.lower()}",
        color=ctx.author.color,
        url=req,
        timestamp=current_time
      )
      # Loops through the word modes and get equivalent cases and values
      for i, word_mode in enumerate(word_modes):
        temp_text = ''
        for ii, case_value in enumerate(case_values):
          line = f"{case_names[ii]} {case_values[ii][i]}\n"
          temp_text += line

        embed.add_field(
          name=word_mode,
          value=f"```apache\n{temp_text}```",
          inline=True)
      await ctx.respond(embed=embed, ephemeral=True)

  @_decline.command(name='finnish', options=[
      Option(str, name='word', description='The word to decline', required=True),
      Option(str, name='word_type', description='The word type', required=True,
        choices=[
            OptionChoice(name="Adjective", value="adjetctive"), OptionChoice(name="Noun", value="noun"),
        ])
    ]
  )
  @commands.cooldown(1, 10, commands.BucketType.user)
  @utils.check_command_limit()
  async def _decline_finnish(self, ctx, word: str = None, word_type: str = None):
    """ Declines a Finnish word; showing a table with its full declension forms. """

    await ctx.defer(ephemeral=True)

    me = ctx.author
    if not word:
      return await ctx.respond(f"**Please {me.mention}, inform a word to search!**", ephemeral=True)
    if not word_type:
      return await ctx.respond("**Inform the word type!**", ephemeral=True)

    if word_type == 'noun':
      root = 'https://cooljugator.com/fin'
    elif word_type == 'adjective':
      root = 'https://cooljugator.com/fia'
    else:
      return await ctx.respond("**Invalid word type!**", ephemeral=True)

    # Request part
    req = f"{root}/{word.lower()}"
    async with self.session.get(req) as response:
      if response.status == 200:

        try:
          # Scraping part
          html = BeautifulSoup(await response.read(), 'html.parser')
          main_div = html.select('#conjugationDivs')
          div = html.select('.conjugation-table.collapsable')
          case_titles = {}
          for d in div:
            case_titles.update({title.text: [] for title in d.select('.conjugation-cell.conjugation-cell-four.tense-title') if title.text})
            
          # Get case names
          case_names = []
          for dd in div:
            case_names.append([case.text for case in dd.select('.conjugation-cell.conjugation-cell-four.conjugation-cell-pronouns.pronounColumn') if case.text])

          indexes = list(case_titles)
          index = indexes[0]
          for dd in div:
            for decl in dd.select('.conjugation-cell.conjugation-cell-four'):
              if decl.text:
                try:
                  if new_i := indexes.index(decl.text):
                    index = indexes[new_i]
                except ValueError:
                  pass
              
                try:
                  case_titles[index].append(decl['data-default'])
                except Exception:
                  pass

        except AttributeError:
          return await ctx.respond("**Nothing found! Make sure to type correct parameters!**", ephemeral=True)

      try:
        current_time = await utils.get_time_now()
        # Embed part
        embed = discord.Embed(
          title=f"Finnish Declension",
          description=f"**Word:** {word}\n**Type:** {word_type}",
          color=ctx.author.color,
          timestamp=current_time,
          url=req
        )
        count = 0
        for key, values in case_titles.items():
          #print(key)
          temp_list = zip_longest(case_names[count], values, fillvalue='')
          temp_text = ''
          for tl in temp_list:
            temp_text += f"{' '.join(tl)}\n"

          embed.add_field(
            name=key,
            value=f"```apache\n{temp_text}```",
            inline=True
          )
          count += 1
        await ctx.respond(embed=embed, ephemeral=True)
      except Exception as e:
        print(e)
        return await ctx.respond("**I couldn't do this request, make sure to type things correctly!**", ephemeral=True)

  @_decline.command(name='german')
  @commands.cooldown(1, 10, commands.BucketType.user)
  @utils.check_command_limit()
  async def german(self, interaction, 
    word: Option(str, name='word', description='The word to decline', required=True)) -> None:
    """ Declines a German word. """

    await interaction.defer(ephemeral=True)

    root = 'https://www.verbformen.com/declension/nouns'
    req = f"{root}/?w={word}"
    async with self.session.get(req) as response:
      if response.status != 200:
        return await interaction.respond("**Something went wrong with that search!**", ephemeral=True)

      html = BeautifulSoup(await response.read(), 'html.parser')
      div = html.select_one('.rAbschnitt')
      decl_type_list = []
      for decl_type in div.select('section.rBox.rBoxWht'):
        try:
          decl_type_list.append(decl_type.select_one('header h2').text)
        except:
          decl_type_list.append('...')
          pass     
      master_dict = {}
      for dt in decl_type_list:
        master_dict[dt] = []

      # Gets the main section of the page
      for section in html.select('.rAbschnitt '):
        # Gets the declination tables
        for i, table in enumerate(section.select('.rAufZu')):
          # Gets the gender blocks of each table
          # print(table.select('.vTbl'))
          for case in table.select('.vTbl'):
            category_name = '...'

            if cat := case.select_one('h2'):
              category_name = cat.text
            elif cat := case.select_one('h3'):
              category_name = cat.text
              
            case_dict = {}
            decl_name = list(master_dict)[i-1]
            #category_name = f"{category_name}
            case_dict[category_name] = []
        
            # Gets each row of each table block
            for row in case.select('tr'):
              case_name = row.select_one('th').text
              case_decl = [line.text for line in row.select('td')]
              case_decl.insert(0, case_name)
              case_dict[category_name].append(case_decl.copy())
              case_decl.clear()
            master_dict[decl_name].append(copy.deepcopy(case_dict))


    master_list = [[k, v] for k, v in master_dict.items()]
    # Additional data:
    additional = {
      'req': req,
      'search': word,
      'change_embed': self.make_german_embed
    }
    view = PaginatorView(master_list, **additional)
    embed = await view.make_embed(interaction.author)
    await interaction.respond(embed=embed, view=view)

  async def make_german_embed(self, req: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
    offset: int, lentries: int, entries: Dict[str, Any], title: str = None, result: str = None) -> discord.Embed:
    """ Makes an embed for the current search example.
    :param req: The request URL link.
    :param member: The member who triggered the command.
    :param search: The search that was performed.
    :param example: The current search example.
    :param offset: The current page of the total entries.
    :param lentries: The length of entries for the given search.
    :param entries: The entries of the search.
    :param title: The title of the search.
    :param result: The result of the search. """

    current_time = await utils.get_time_now()

    # print(example)

    template = example
    title = template[0]
    embed = discord.Embed(
      title=f"Declension table - ({title})",
      description=f"**Word:** {search}",
      color=member.color,
      timestamp=current_time,
      url=req)

    for gender_dict in template[1]:
      for key, values in gender_dict.items():
        text = ''
        for row in values:
          text += f"{' '.join(row)}\n"
        
        embed.add_field(
          name=key,
          value=f"```apache\n{text}```",
          inline=True
        )
    # Sets the author of the search
    embed.set_author(name=member, icon_url=member.display_avatar)
    # Makes a footer with the a current page and total page counter
    embed.set_footer(text=f"{offset}/{lentries}", icon_url=member.guild.icon.url)

    return embed
        
      

def setup(client):
  client.add_cog(Declension(client))