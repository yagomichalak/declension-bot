import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from itertools import zip_longest


class Conjugation(commands.Cog):
  """ A category for conjugation commands. """

  def __init__(self, client) -> None:
    """ Init method of the conjugation class. """
    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)


  @commands.Cog.listener()
  async def on_ready(self):
    print('Something cog is online!')


  @commands.command(aliases=['nl'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def dutch(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Dutch.\n:param verb: The verb to conjugate.```
    
    🇳🇱 __**Example:**__
    ```ini\n[1] dec!dutch hebben\n[2] dec!nl leren\n[3] dec!dutch verlaten\n[4] dec!nl horen"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://www.mijnwoordenboek.nl/werkwoord/{verb}'
    async with self.session.get(root) as response:
      if response.status != 200:
        return await ctx.send("**Something went wrong with that search!**")

    
      # Gets the html, the conjugation table div and table
      html = BeautifulSoup(await response.read(), 'html.parser')
      content_box = html.select_one('.content_box')
      table_rows = [row for row in content_box.select('table tr')[1:]]
      lenro = len(table_rows)
      if lenro == 0:
        return await ctx.send("**Nothing found for the informed value!**")

      # Creates the initial embed
      embed = discord.Embed(
        title="Dutch Conjugation",
        color=ctx.author.color,
        timestamp=ctx.message.created_at,
        url=root
      )
      msg = await ctx.send(embed=discord.Embed(title='🇳🇱'))
      await msg.add_reaction('⬅️')
      await msg.add_reaction('➡️')
      index = 0
      # Loops through each row of the conjugation tables
      while True:
        embed.title = f"Dutch Conjugation ({round(lenro/(lenro-index))}/{round(lenro/11)})"
        for i in range(0, 12, 2):
          if index + i + 1< len(table_rows):
            tense_name = table_rows[index+i].get_text().strip()
            conjugation = table_rows[index+i+1].get_text().strip().split('  ')
            conjugation = '\n'.join(conjugation)
          else:
            break

          # Adds a field for each table
          embed.add_field(
            name=tense_name,
            value=f"```apache\n{conjugation}```",
            inline=True
          )

        await msg.edit(embed=embed)
        embed.clear_fields()
        # Waits for user response to switch the page
        try:
          reaction, user = await self.client.wait_for('reaction_add', timeout=60, check=lambda r, u: r.message.id == msg.id and u.id == ctx.author.id and \
          str(r.emoji) in ['⬅️', '➡️']
          )
        except asyncio.TimeoutError:
          await msg.remove_reaction('⬅️', self.client.user)
          await msg.remove_reaction('➡️', self.client.user)
          break
        else:
          if str(reaction.emoji) == "➡️":
              await msg.remove_reaction(reaction.emoji, user)
              if index + 11 <= len(table_rows) / 2:
                  index += 12
              continue
          elif str(reaction.emoji) == "⬅️":
              await msg.remove_reaction(reaction.emoji, user)
              if index > 0:
                  index -= 12
              continue
  

  # Conjugators based on Reverso's website
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.command(aliases=['jp', 'ja', 'jap'])
  async def japanese(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Japanese.\n:param verb: The verb to conjugate.```
    
    🇯🇵 __**Example:**__
    ```ini\n[1] dec!japanese 食べる\n[2] dec!jp kurasu\n[3] dec!ja 分かる\n[4] dec!jap kangaeru"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-japanese-verb-{temp_verb}.html'
    emoji_title = '🇯🇵'
    return await self.conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Japanese', space=True, aligned=False)

  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.command(aliases=['sa', 'ar'])
  async def arabic(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Arabic.\n:param verb: The verb to conjugate.```
    
    🇸🇦-🇪🇬 __**Example:**__
    ```ini\n[1] dec!arabic احضار\n[2] dec!sa Hakama\n[3] dec!ar ʾakhadha\n[4] dec!arabic فَعَلَ"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-arabic-verb-{temp_verb}.html'
    emoji_title = '🇸🇦-🇪🇬'
    return await self.conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Arabic', space=True, aligned=False)

  @commands.command(aliases=['pt', 'portugais', 'portugués', 'português'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def portuguese(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Portuguese.\n:param verb: The verb to conjugate.```
    
    🇧🇷-🇵🇹 __**Example:**__
    ```ini\n[1] dec!portuguese ser\n[2] dec!pt estar\n[3] dec!portugais ir\n[4] dec!portugués fazer"""

    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
    emoji_title = '🇧🇷-🇵🇹'
    language_title = 'Portuguese'
    # return await self.conjugate(ctx=ctx, root=root, 
    # verb=verb, emoji_title=emoji_title)

    async with self.session.get(root) as response:
      if response.status != 200:
        return await ctx.send("**Something went wrong with that search!**")

    
      # Gets the html and the table div
      html = BeautifulSoup(await response.read(), 'html.parser')
      subhead = html.select_one('.subHead.subHead-res.clearfix')
      if not subhead:
        return await ctx.send("**Invalid request!**")

      # Translation options
      #-> Word translation
      tr_div = subhead.select_one('.word-transl-options')
      found_verb = tr_div.select_one('.targetted-word-wrap').get_text().strip()

      embed = discord.Embed(
        title="English Conjugation",
        description=f"""**Searched:** {verb}
        **Found:** {found_verb}""",
        color=ctx.author.color,
        timestamp=ctx.message.created_at,
        url=root
      )
      embed.set_footer(
        text=f"Requested by {ctx.author}",
        icon_url=ctx.author.avatar_url)


      # Conjugation table divs
      verb_div = html.select_one('.word-wrap')
      word_wraps = verb_div.select_one('.result-block-api')
      word_wrap_rows = word_wraps.select('.word-wrap-row')

      index = 0
      tense_title = ''

      # Sends initial embed and adds the arrow emojis to it
      msg = await ctx.send(embed=discord.Embed(
        title=emoji_title))
      await msg.add_reaction('⬅️')
      await msg.add_reaction('➡️')
      await asyncio.sleep(0.5)

      while True:
        current_row = word_wrap_rows[index]
        embed.title = f"{language_title} Conjugation ({index+1}/{len(word_wrap_rows)})"
        embed.clear_fields()

        # Loops through the rows
        for table in current_row.select('.wrap-three-col'):
          # Specifies the verbal tense if there is one
          if temp_tense_name := table.select_one('p'):
            tense_name = temp_tense_name.get_text()

            # Changes verbal mode if it's time to change it
            if (temp_title := current_row.select_one('.word-wrap-title')):
              title = temp_title.get_text().strip()
            verbal_mode = title
          # If there isn't, it shows '...' instead
          else:
            tense_name = '...'
            verbal_mode = table.select_one('.word-wrap-title').get_text().strip()

          temp_text = ""

          # Loops through each tense row
          for li in table.select('.wrap-verbs-listing li'):
            # Makes a temp text with all conjugations
            temp_text += f"{li.get_text(separator=' ')}\n"
          # Specifies the verbal mode
          temp_text += f"""\nmode="{verbal_mode}"\n"""
          embed.add_field(
            name=tense_name,
            value=f"```apache\n{temp_text}```",
            inline=True
          )
          # Sends to Discord the current state of the embed
          await msg.edit(embed=embed)

        # Waits for user reaction to switch pages
        try:
          r, u = await self.client.wait_for(
            'reaction_add', timeout=60, 
            check=lambda r, u: r.message.id == msg.id and \
            u.id == ctx.author.id and str(r.emoji) in ['⬅️', '➡️']
          )
        except asyncio.TimeoutError:
          await msg.remove_reaction('⬅️', self.client.user)
          await msg.remove_reaction('➡️', self.client.user)
          return
        else:
          if str(r.emoji) == '⬅️':
            if index > 0:
              index -= 1
            await msg.remove_reaction(r, u)
            continue
          else:
            if index < len(word_wrap_rows) - 1:
              index += 1
            await msg.remove_reaction(r, u)
            continue


  @commands.command(aliases=['it', 'italiano', 'italien', 'ita'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def italian(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Italian.\n:param verb: The verb to conjugate.```
    
    🇮🇹-🇨🇭 __**Example:**__
    ```ini\n[1] dec!italian trovare\n[2] dec!it essere\n[3] dec!italiano avere\n[4] dec!italien finire"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-italian-verb-{temp_verb}.html'
    emoji_title = '🇮🇹-🇨🇭'
    return await self.conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Italian')

  @commands.command(aliases=['fr', 'français', 'francés', 'francais', 'francês', 'frances'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def french(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in French.\n:param verb: The verb to conjugate.```
    
    🇫🇷-🇧🇪 __**Example:**__
    ```ini\n[1] dec!french être\n[2] dec!fr avoir\n[3] dec!français faire\n[4] dec!francés lire"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-french-verb-{temp_verb}.html'
    emoji_title = '🇫🇷-🇧🇪'
    return await self.conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='French')
  
  @commands.command(aliases=['es', 'esp', 'español', 'espanhol', 'espagnol', 'espanol'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def spanish(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Spanish.\n:param verb: The verb to conjugate.```
    
    🇪🇸-🇲🇽 __**Example:**__
    ```ini\n[1] dec!spanish hacer\n[2] dec!es tener\n[3] dec!español estoy\n[4] dec!espagnol stoy"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-spanish-verb-{temp_verb}.html'

    emoji_title = '🇪🇸-🇲🇽'
    return await self.conjugate(ctx=ctx, root=root, 
  verb=verb, emoji_title=emoji_title, language_title='Spanish')


  @commands.command(aliases=['en', 'eng', 'ing', 'inglés', 'ingles'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def english(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in English.\n:param verb: The verb to conjugate.```
    
    🇺🇸-🇬🇧 __**Example:**__
    ```ini\n[1] dec!english make\n[2] dec!en to do\n[3] dec!eng get\n[4] dec!inglés to guess"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-english-verb-{temp_verb}.html'
    emoji_title = "🇺🇸-🇬🇧"
    return await self.conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='English')


  async def conjugate(self, ctx, root: str, verb: str, emoji_title: str, language_title: str) -> None:
    """ Conjugates a verb.
    :param root: The language endpoint from which to do the HTTP request.
    :param verb: The verb that is being conjugated.
    """
    async with self.session.get(root) as response:
      if response.status != 200:
        return await ctx.send("**Something went wrong with that search!**")

    
      # Gets the html and the table div
      html = BeautifulSoup(await response.read(), 'html.parser')
      subhead = html.select_one('.subHead.subHead-res.clearfix')
      if not subhead:
        return await ctx.send("**Invalid request!**")

      # Translation options
      #-> Word translation
      tr_div = subhead.select_one('.word-transl-options')
      found_verb = tr_div.select_one('.targetted-word-wrap').get_text().strip()

      embed = discord.Embed(
        title="English Conjugation",
        description=f"""**Searched:** {verb}
        **Found:** {found_verb}""",
        color=ctx.author.color,
        timestamp=ctx.message.created_at,
        url=root
      )
      embed.set_footer(
        text=f"Requested by {ctx.author}",
        icon_url=ctx.author.avatar_url)


      # Conjugation table divs
      verb_div = html.select_one('.word-wrap')
      word_wraps = verb_div.select_one('.result-block-api')
      word_wrap_rows = word_wraps.select('.word-wrap-row')

      index = 0
      tense_title = ''

      # Sends initial embed and adds the arrow emojis to it
      msg = await ctx.send(embed=discord.Embed(
        title=emoji_title))
      await msg.add_reaction('⬅️')
      await msg.add_reaction('➡️')
      await asyncio.sleep(0.5)

      while True:
        current_row = word_wrap_rows[index]
        embed.title = f"{language_title} Conjugation ({index+1}/{len(word_wrap_rows)})"
        embed.clear_fields()

        # Loops through the rows
        for table in current_row.select('.wrap-three-col'):
          # Specifies the verbal tense if there is one
          if temp_tense_name := table.select_one('p'):
            tense_name = temp_tense_name.get_text()

            # Changes verbal mode if it's time to change it
            if (temp_title := current_row.select_one('.word-wrap-title')):
              title = temp_title.get_text().strip()
            verbal_mode = title
          # If there isn't, it shows '...' instead
          else:
            tense_name = '...'
            verbal_mode = table.select_one('.word-wrap-title').get_text().strip()

          temp_text = ""

          # Loops through each tense row
          for li in table.select('.wrap-verbs-listing li'):
            # Makes a temp text with all conjugations
            temp_text += f"{li.get_text()}\n"
          # Specifies the verbal mode
          temp_text += f"""\nmode="{verbal_mode}"\n"""
          embed.add_field(
            name=tense_name,
            value=f"```apache\n{temp_text}```",
            inline=True
          )
          # Sends to Discord the current state of the embed
          await msg.edit(embed=embed)

        # Waits for user reaction to switch pages
        try:
          r, u = await self.client.wait_for(
            'reaction_add', timeout=60, 
            check=lambda r, u: r.message.id == msg.id and \
            u.id == ctx.author.id and str(r.emoji) in ['⬅️', '➡️']
          )
        except asyncio.TimeoutError:
          await msg.remove_reaction('⬅️', self.client.user)
          await msg.remove_reaction('➡️', self.client.user)
          return
        else:
          if str(r.emoji) == '⬅️':
            if index > 0:
              index -= 1
            await msg.remove_reaction(r, u)
            continue
          else:
            if index < len(word_wrap_rows) - 1:
              index += 1
            await msg.remove_reaction(r, u)
            continue



def setup(client) -> None:
  client.add_cog(Conjugation(client))