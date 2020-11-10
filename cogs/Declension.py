import discord
from discord.ext import commands
import aiohttp
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

class Declension(commands.Cog):
  '''
  A category for word declensions.
  '''

  def __init__(self, client):
    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)
    self.pdf_token = getenv('PDF_API_TOKEN')

  @commands.Cog.listener()
  async def on_ready(self):
    print('Declension cog is online!')

  @commands.group(aliases=['dec', 'decl', 'declination'])
  async def decline(self, ctx):
    """ A command for declinating specific languages.
    
    PS: Since we have 2 dinstinct commands (conjugation, declension) for some languages,
    we will need to use this for specifying which one we want to use.```
    
    __**Example:**__
    ```ini\n[Declension] dec!dec polish kobieta\n[Conjugation] dec!conj polish dać"""
    if ctx.invoked_subcommand:
      return

    cmd = self.client.get_command('decline')
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

  
  @decline.command(aliases=['polski', 'pl', 'pol', 'po'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def polish(self, ctx, word: str = None):
    """Declines a Polish word; showing a table with its full declension forms.\n:param word: The word to decline.```
    
    🇵🇱 __**Example:**__
    ```ini\n[1] dec!dec polish kobieta\n[2] dec!dec po mężczyzna\n[3] dec!dec polski warzywa\n[4] dec!dec pol przyjaciel"""
    me = ctx.author
    if not word:
      return await ctx.send(f"**Please {me.mention}, inform a word to search!**")

    root = 'http://online-polish-dictionary.com/word'

    async with ctx.typing():
      async with self.session.get(f"{root}/{word}") as response:
        if response.status == 200:
          data = await response.text()

          output = ''
          start = 'https://e-polish.eu/dictionary/en/'
          end = '.pdf'
          s = data.find(start)
          e = data.find(end)
          #print(data)
          url = data[s:e+4]

        else:
          return await ctx.send("**For some reason I couldn't process it!**")
      async with self.session.get(url) as response:
        #response = requests.get(url)
        if response.status == 200:
          try:
            with open(f'files/{me.id}.pdf', 'wb') as f:
              f.write(await response.read())
          except Exception:
            return await ctx.send("**I couldn't find anything for that word!**")
        else:
          # print(error)
          return await ctx.send("**For some reason I couldn't process it!**")
      

    
      convertapi.api_secret = self.pdf_token
      convertapi.convert('png', {
      'File': f'./files/{me.id}.pdf',  
  }, from_format = 'pdf').save_files('./files')

      # Opens a image in RGB mode 
      im = Image.open(rf"files/{me.id}.png") 
        
      # Size of the image in pixels (size of orginal image) 
      # (This is not mandatory) 
      width, height = im.size 
        
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



      await ctx.send(file=discord.File(f'files/{me.id}.png'))
      os.remove(f"files/{me.id}.pdf")
      os.remove(f"files/{me.id}.png")    
  
  
  @commands.command(aliases=['ruski', 'ru', 'rus', 'русский'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def russian(self, ctx, word: str = None):
    """Declines a Russian word; showing a table with its full declension forms.\n:param word: The word to decline.```
    
    🇷🇺 __**Example:**__
    ```ini\n[1] dec!russian год\n[2] dec!ruski красивый\n[3] dec!ru такой\n[4] dec!rus эмоциональный"""
    if not word:
      return await ctx.send("**Please, type a word**")

    root = 'https://en.openrussian.org/ru'

    req = f"{root}/{word.lower()}"
    async with self.session.get(req) as response:
      if response.status != 200:
        return await ctx.send("**Something went wrong with that search!**")

    
      # Gets the html and the table div
      html = BeautifulSoup(await response.read(), 'html.parser')
      div = html.select_one('.table-container')

      if not div:
        return await ctx.send("**I couldn't find anything for this!**")

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
        return await ctx.send("**I can't decline this word, maybe this is a verb!**")
      # Gets all case names
      case_names = [case.text.strip() for case in div.select('tbody tr th .short') if case.text]
      # Gets all values
      case_values = []
      for case in div.select('tbody tr'):
        row_values = []
        for row in case.select('td'):
          print(row.get_text("", strip=True))
          if value := row.get_text(" | ", strip=True):
            row_values.append(value.strip())

        case_values.append(row_values)


      tds = [td for td in div.select('tbody tr')]
      word_type = html.select_one('.info').get_text(", ", strip=True)
      # Makes the embedded message
      embed = discord.Embed(
        title="Russian Declension",
        description=f"**Word:** {word.lower()}\n**Description:** {word_type}",
        color=ctx.author.color,
        url=req,
        timestamp=ctx.message.created_at
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
      await ctx.send(embed=embed)

  @commands.command(aliases=['fi', 'fin', 'suomi'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def finnish(self, ctx, word: str = None, word_type: str = None):
    """Declines a Finnish word; showing a table with its full declension forms.\n:param word: The word to decline.\n:param word_type: The type of the word (noun/adj)```
    
    🇫🇮 __**Example:**__
    ```ini\n[1] dec!finnish erilainen adjective\n[2] dec!suomi kallis adjn\n[3] dec!fi aika noun\n[4] dec!fin kansa n"""
    me = ctx.author
    if not word:
      return await ctx.send(f"**Please {me.mention}, inform a word to search!**")
    if not word_type:
      return await ctx.send("**Inform the word type!**")

    if word_type.lower() in ['noun', 'n']:
      root = 'https://cooljugator.com/fin'
    elif word_type.lower() in ['adjective', 'adj']:
      root = 'https://cooljugator.com/fia'
    else:
      return await ctx.send("**Invalid word type!**")    

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
          return await ctx.send("**Nothing found! Make sure to type correct parameters!**")

      try:
        # Embed part
        embed = discord.Embed(
          title=f"Finnish Declension",
          description=f"**Word:** {word}\n**Type:** {word_type}",
          color=ctx.author.color,
          timestamp=ctx.message.created_at,
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
        await ctx.send(embed=embed)
      except Exception:
        return await ctx.send("**I couldn't do this request, make sure to type things correctly!**")

  @decline.command(aliases=['deutsch', 'ger', 'de'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def german(self, ctx, word: str = None):
    """Declines a German word; showing a table with its full declension forms.\n:param word: The word to decline.```
    
    🇩🇪 __**Example:**__
    ```ini\n[1] dec!dec german mann\n[2] dec!dec de groß\n[3] dec!dec deutsch lecker\n[4] dec!dec ger frau"""
    if not word:
      return await ctx.send("**Inform a word to decline!**")

    root = 'https://www.verbformen.com/declension/'
    req = f"{root}/?w={word}"
    async with self.session.get(req) as response:
      if not response.status == 200:
        return await ctx.send("**Something went wrong with that search!**")

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

      #print(master_dict)

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

    def check(r, u):
      if u.id == ctx.author.id and r.message.id == msg.id and str(r.emoji) in ['⬅️', '➡️']:
        return True
      else:
        return False

    master_list = [[k, v] for k, v in master_dict.items()]
    user_index = 0
    lenmaster = len(master_list)
    msg = await ctx.send(embed=discord.Embed(title='🇩🇪'))
    await asyncio.sleep(0.5)
    await msg.add_reaction('⬅️')
    await msg.add_reaction('➡️')
    while True:
      template = master_list[user_index]
      title = template[0]
      new_embed = discord.Embed(
        title=f"Declension table - ({title})",
        description=f"**Word:** {word}",
        color=ctx.author.color,
        timestamp=ctx.message.created_at,
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
      await msg.edit(embed=new_embed)
      try: 
        reaction, user = await self.client.wait_for('reaction_add', timeout=60, check=check)
      except asyncio.TimeoutError:
        await msg.remove_reaction('➡️', self.client.user)
        await msg.remove_reaction('⬅️', self.client.user)
      else:
        emoji = str(reaction.emoji)
        await msg.remove_reaction(emoji, user)
        if emoji == '⬅️':
          if user_index > 0:
            user_index -= 1
          continue

        elif emoji == '➡️':
          if user_index < lenmaster -1:
            user_index += 1
          continue

        
      

def setup(client):
  client.add_cog(Declension(client))