import discord
from discord.ext import commands
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

class Declension(commands.Cog):

  def __init__(self, client):
    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)
    self.pdf_token = getenv('PDF_API_TOKEN')
  
  @commands.command()
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def pl(self, ctx, word: str = None):
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
          url = data[s:e+4]
          #print(url)

        else:
          return await ctx.send("**For some reason I couldn't process it!**")

      async with self.session.get(url) as response:
        #response = requests.get(url)
        if response.status == 200:
          try:
            with open(f'pf/{me.id}.pdf', 'wb') as f:
              f.write(await response.read())
          except Exception:
            return await ctx.send("**I couldn't find anything for that word!**")
        else:
          print(error)
          return await ctx.send("**For some reason I couldn't process it!**")
      

    
      convertapi.api_secret = self.pdf_token
      convertapi.convert('png', {
      'File': f'./pf/{me.id}.pdf',  
  }, from_format = 'pdf').save_files('./pf')

      # Opens a image in RGB mode 
      im = Image.open(rf"pf/{me.id}.png") 
        
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
      im1.save(f'pf/{me.id}.png')



      await ctx.send(file=discord.File(f'pf/{me.id}.png'))
      os.remove(f"pf/{me.id}.pdf")
      os.remove(f"pf/{me.id}.png")


  @commands.command()
  @commands.has_permissions(administrator=True)
  async def test(self, ctx):
    pass


  @staticmethod
  async def database():
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


  @commands.command()
  @commands.has_permissions(administrator=True)
  async def aa(self, ctx, word: str = None, type: str = None):
    if not word:
      return await ctx.send("**Inform a word to decline!**")
    if not type:
      type = 'noun'

    root = 'https://www.verbformen.com/declension/'

    async with self.session.get(f"{root}/{type}/?w={word}") as response:
      if not response.status == 200:
        return await ctx.send("**Something went wrong with that search!**")

      embed_table = discord.Embed(
        title=f"__Declination Table__",
        description=f'''
        **Word:** {word.title()}
        **Type of word:** {type}
        ''',
        color=ctx.author.color
      )

      html = BeautifulSoup(await response.read(), 'html.parser')
      for case in html.select('.vTbl'):
        category_name = case.select_one('h3').text
        #print(category_name)
        #table_block = []
        case_dict = {}
        case_dict[category_name] = []
        for row in case.select('tr'):
          case_name = row.select_one('th').text
          case_decl = [line.text for line in row.select('td')]
          case_decl.insert(0, case_name)
          case_dict[category_name].append(case_decl.copy())
          case_decl.clear()
          
              
        for key, values in case_dict.items():
          print(key)
          row_text = ''
          for row_list in values:
            row_text += f"{' '.join(row_list)}\n"

          embed_table.add_field(
            name=key,
            value=f"```apache\n{row_text}```",
            inline=True
          )

      await ctx.send(embed=embed_table)

  @commands.command(aliases=['german', 'ger', 'de'])
  @commands.has_permissions(administrator=True)
  async def deutsch(self, ctx, word: str = None, type: str = None):
    if not word:
      return await ctx.send("**Inform a word to decline!**")
    if not type:
      type = 'noun'

    root = 'https://www.verbformen.com/declension/'

    async with self.session.get(f"{root}/{type}/?w={word}") as response:
      if not response.status == 200:
        return await ctx.send("**Something went wrong with that search!**")

      embed_table = discord.Embed(
        title=f"__Declension Table__",
        description=f'''
        **Word:** {word.title()}
        **Type of word:** {type}
        ''',
        color=ctx.author.color
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
        description=f"**Word:** {word}\n**Type:** {type}",
        color=ctx.author.color,
        timestamp=ctx.message.created_at)
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