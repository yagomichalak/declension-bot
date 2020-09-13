import discord
from discord.ext import commands, tasks
import aiohttp
import aiomysql
from os import getenv
import asyncio
import json
from datetime import datetime
import re
import requests
#from wand.image import Image as wi
import convertapi
from PIL import Image
import time
from bs4 import BeautifulSoup
import copy
from itertools import zip_longest, cycle

status = cycle(['Russian', 'German'])

class Declension(commands.Cog):

  def __init__(self, client):
    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)
    self.pdf_token = getenv('PDF_API_TOKEN')

  @commands.Cog.listener()
  async def on_ready(self):
    self.change_status.start()
    print('Declension cog is online!')

  @tasks.loop(seconds=30)
  async def change_status(self):
    await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"{next(status)} declensions!"))
    
  
  @commands.command(hidden=True, aliases=['polish', 'pl', 'pol'])
  @commands.is_owner()
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def polski(self, ctx, word: str = None):
    '''
    Declines a Polish word; showing a table with its full declension forms.
    :param word: The word to decline.
    '''
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
          print(data)
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
          print(error)
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


  @commands.command(hidden=True)  
  @commands.is_owner()
  #@commands.cooldown(1, 10, commands.BucketType.user)
  async def pl2(self, ctx, word: str = None):
    '''
    (PS) This command might not work, in fact, it hardly will.

    Declines a Polish word; showing a table with its full declension forms.
    :param word: The word to decline.
    '''
    me = ctx.author
    if not word:
      return await ctx.send(f"**Please {me.mention}, inform a word to search!**")

    #root2 = 'https://www.declinator.com/?word'

    #root = 'http://online-polish-dictionary.com/word'
    root3 = f'http://aztekium.pl/przypadki.py?szukaj={word}&lang=en'

    # Request part
    async with self.session.get(root3) as response:
      if response.status == 200:


        # Embed
        embed = discord.Embed(
          title=f"Polish Declension",
          description=f"**Word:** {word}",
          color=ctx.author.color,
          timestamp=ctx.message.created_at
        )

        # Scraping part
        html = BeautifulSoup(await response.read(), 'html.parser')
        div = html.select(
        'body center:nth-child(1) form:nth-child(1) table:nth-child(3) tbody:nth-child(1) tr:nth-child(1) td:nth-child(2)')
        text = ''
        for sub in div:
          for i, tr in enumerate(sub.select('table:nth-child(9) tr')):
            tds = tr.select('td')
            tds = tds[:3:2]
            beginning, ending = tds[0].select('b')
            text += f'{beginning.text} = "{ending.text}"\n'


        #print(text)
        if text:
          embed.add_field(
            name="All cases",
            value=f"```apache\n{text}```")
          await ctx.send(embed=embed)
    
  
  @commands.command(aliases=['russian', 'ru', 'rus'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def ruski(self, ctx, word: str = None, word_type: str = None):
    '''
    Declines a Russian word; showing a table with its full declension forms.
    :param word: The word to decline.
    '''
    me = ctx.author
    if not word:
      return await ctx.send(f"**Please {me.mention}, inform a word to search!**")
    if not word_type:
      return await ctx.send("**Inform the word type!**")

    if word_type.lower() in ['noun', 'n']:
      root = 'https://cooljugator.com/run'
    elif word_type.lower() in ['adjective', 'adj']:
      root = 'https://cooljugator.com/rua'
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
          div = html.select_one('.conjugation-table.collapsable')
          case_titles = {title.text: [] for title in div.select('.conjugation-cell.conjugation-cell-four.tense-title') if title.text}
          print(f"{case_titles=}")
          case_names = [case.text for case in div.select('.conjugation-cell.conjugation-cell-four.conjugation-cell-pronouns.pronounColumn') if case.text]
          indexes = list(case_titles)
          index = indexes[0]
          for decl in div.select('.conjugation-cell.conjugation-cell-four'):
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

        # Embed part
        embed = discord.Embed(
          title=f"Russian Declension",
          description=f"**Word:** {word}",
          color=ctx.author.color,
          timestamp=ctx.message.created_at,
          url=req
        )
        for key, values in case_titles.items():
          print(key)
          temp_list = zip_longest(case_names, values, fillvalue='')
          temp_text = ''
          for tl in temp_list:
            temp_text += f"{' '.join(tl)}\n"

          embed.add_field(
            name=key,
            value=f"```apache\n{temp_text}```",
            inline=True
          )
        await ctx.send(embed=embed)

  @commands.command(aliases=['fi', 'fin'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def finnish(self, ctx, word: str = None, word_type: str = None):
    '''
    Declines a Finnish word; showing a table with its full declension forms.
    :param word: The word to decline.
    '''
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
            
          print(f"{case_titles=}")
          case_names = []
          for dd in div:
            case_names.append([case.text for case in dd.select('.conjugation-cell.conjugation-cell-four.conjugation-cell-pronouns.pronounColumn') if case.text])
            print()
            print(f"{case_names=}")
            print()
          print()
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
          print()
          print(f"{case_titles=}")
        except AttributeError:
          return await ctx.send("**Nothing found! Make sure to type correct parameters!**")

        # Embed part
        embed = discord.Embed(
          title=f"Finnish Declension",
          description=f"**Word:** {word}",
          color=ctx.author.color,
          timestamp=ctx.message.created_at,
          url=req
        )
        for key, values in case_titles.items():
          print(key)
          for i, case_name_list in enumerate(case_names):
            temp_list = zip_longest(case_names[i], values, fillvalue='')
            temp_text = ''
            for tl in temp_list:
              temp_text += f"{' '.join(tl)}\n"

            embed.add_field(
              name=key,
              value=f"```apache\n{temp_text}```",
              inline=True
            )
        await ctx.send(embed=embed)


  @staticmethod
  async def database():
    '''
    A database entry, in case I need some in the future.
    '''
    loop = asyncio.get_event_loop()
    db = await aiomysql.connect(
      host=getenv('DB_HOST'), 
      user=getenv('DB_USER'), 
      password=getenv('DB_PASSWORD'), 
      db=getenv('DB_NAME'), 
      loop=loop
      )

    mycursor = await db.cursor()
    return mycursor, db


  

  @commands.command(aliases=['german', 'ger', 'de'])
  async def deutsch(self, ctx, word: str = None):
    '''
    Declines a German word; showing an embedded message with its full declension forms.
    :param word: The word to decline.
    '''
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