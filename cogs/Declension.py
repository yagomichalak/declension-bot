import discord
from discord.ext import commands
from discord import slash_command, option, Option, OptionChoice, SlashCommandGroup

import aiohttp
import os
from os import getenv
import asyncio
import json
from datetime import datetime
import re
import requests
import convertapi
from PIL import Image
import time
from bs4 import BeautifulSoup
import copy
from itertools import zip_longest
from others import utils

TEST_GUILDS = [459195345419763713, 777886754761605140]

class Declension(commands.Cog):
  '''
  A category for word declensions.
  '''

  def __init__(self, client):
    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)
    self.pdf_token = getenv('PDF_API_TOKEN')

  decline = SlashCommandGroup("decline", "Declines a word in a given language", guild_ids=TEST_GUILDS)

  @commands.Cog.listener()
  async def on_ready(self):
    print('Declension cog is online!')

  @decline.command(name='polish', choices=[
      Option(str, name='word', description='The word to decline', required=True)
    ]
  )
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def _decline_polish(self, ctx, word: str = None):

    await ctx.response.defer()

    me = ctx.author
    if not word:
      return await ctx.response.send(f"**Please {me.mention}, inform a word to search!**", ephemeral=True)

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
  
  @decline.command(name='russian', options=[
      Option(str, name='word', description='The word to decline', required=True)
    ]
  )
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def _decline_russian(self, ctx, word: str = None):
    """ Declines a Russian word; showing a table with its full declension forms. """
    await ctx.defer()

    if not word:
      return await ctx.send("**Please, type a word**", ephemeral=True)

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
        timestamp=ctx.created_at
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

#   # @decline.command(aliases=['fi', 'fin', 'suomi'])
#   # @commands.cooldown(1, 5, commands.BucketType.user)
  @decline.command(name='finnish', options=[
      Option(str, name='word', description='The word to decline', required=True),
      Option(str, name='word_type', description='The word type', required=True,
        choices=[
            OptionChoice(name="Adjective", value="adjetctive"), OptionChoice(name="Noun", value="noun"),
        ])
    ]
  )
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def _decline_finnish(self, ctx, word: str = None, word_type: str = None):
    """ Declines a Finnish word; showing a table with its full declension forms. """

    await ctx.defer()

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

#   # @decline.command(aliases=['deutsch', 'ger', 'de'])
#   # @commands.cooldown(1, 5, commands.BucketType.user)
  # @cog_ext.cog_subcommand(
  #   base='decline', name='german',
  #   description="Declines a German word; showing a table with its full declension forms", options=[
  #     create_option(name='word', description='The word to decline', option_type=3, required=True)
  #   ]
  # )
  # @commands.cooldown(1, 10, commands.BucketType.user)
  async def german(self, ctx, word: str):

    await ctx.defer(ephemeral=True)

    root = 'https://www.verbformen.com/declension/nouns'
    req = f"{root}/?w={word}"
    async with self.session.get(req) as response:
      if response.status != 200:
        return await ctx.respond("**Something went wrong with that search!**", ephemeral=True)

      embed_table = discord.Embed(
        title=f"__Declension Table__",
        description=f'''
        **Word:** {word.title()}''',
        color=ctx.author.color,
        url = req
      )

      html = BeautifulSoup(await response.read(), 'html.parser')
      div = html.select_one('.rAbschnitt')
      decl_type_list = []
      for decl_type in div.select('section.rBox.rBoxWht'):
        try:
          decl_type_list.append(decl_type.select_one('header h2').text)
        except:
          pass     
      master_dict = {}
      for dt in decl_type_list:
        master_dict[dt] = []

      # Gets the main section of the page
      for section in html.select('.rAbschnitt '):
        # Gets the declination tables
        for i, table in enumerate(section.select('.rAufZu')):
          # Gets the gender blocks of each table
          for case in table.select('.vTbl'):
            category_name = case.select_one('h3').text
            index = 0
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
              
            for key, values in case_dict.items():
              row_text = ''
              for row_list in values:
                row_text += f"{' '.join(row_list)}\n"

              embed_table.add_field(
                name=key,
                value=f"```apache\n{row_text}```",
                inline=True
              )
            master_dict[decl_name].append(copy.deepcopy(case_dict))


    master_list = [[k, v] for k, v in master_dict.items()]
    user_index = 0
    lenmaster = len(master_list)

    button_ctx = None

    paginator_view: discord.ui.View = discord.ui.View(timeout=None)
    paginator_view.add_item(discord.ui.Button(style=discord.ButtonStyle.blurple, label="Left", custom_id="left_btn"))
    paginator_view.add_item(discord.ui.Button(style=discord.ButtonStyle.blurple, label="Right", custom_id="right_btn"))

    current_time = await utils.get_time_now()
    while True:
      template = master_list[user_index]
      title = template[0]
      new_embed = discord.Embed(
        title=f"Declension table - ({title})",
        description=f"**Word:** {word}",
        color=ctx.author.color,
        timestamp=current_time,
        url=req)

      for gender_dict in template[1]:
        for key, values in gender_dict.items():
          text = ''
          for row in values:
            text += f"{' '.join(row)}\n"
          
          new_embed.add_field(
            name=key,
            value=f"```apache\n{text}```",
            inline=True
          )
      if button_ctx is None:
        await ctx.respond(embed=new_embed, view=paginator_view, ephemeral=True)
        # Wait for someone to click on them
        button_ctx = await wait_for_component(self.client, view=paginator_view)
      else:
        await button_ctx.edit_origin(embed=new_embed, view=paginator_view)
        # Wait for someone to click on them
        button_ctx = await wait_for_component(self.client, view=paginator_view, messages=button_ctx.origin_message_id)

      await button_ctx.defer(edit_origin=True)

      if button_ctx.custom_id == 'left_btn':
        if user_index > 0:
          user_index -= 1
        continue

      elif button_ctx.custom_id == 'right_btn':
        if user_index < lenmaster -1:
          user_index += 1
        continue

        
      

def setup(client):
  client.add_cog(Declension(client))