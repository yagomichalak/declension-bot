import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from itertools import zip_longest, cycle


class Conjugation(commands.Cog):
  """ A category for conjugation commands. """

  def __init__(self, client) -> None:
    """ Init method of the conjugation class. """
    self.client = client
    self.session = aiohttp.ClientSession(loop=client.loop)


  @commands.Cog.listener()
  async def on_ready(self):
    print('Something cog is online!')

  @commands.group(aliases=['conj', 'con', 'cj'])
  async def conjugate(self, ctx):
    """ A command for conjugating specific languages.
    
    PS: Since we have 2 dinstinct commands (conjugation, declension) for some languages,
    we will need to use this for specifying which one we want to use.```
    
    __**Example:**__
    ```ini\n[Declension] dec!dec polish kobieta\n[Conjugation] dec!conj polish dać"""
    if ctx.invoked_subcommand:
      return

    cmd = self.client.get_command('conjugate')
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


  @commands.command(aliases=['nl'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def dutch(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Dutch.\n:param verb: The verb to conjugate.```
    
    🇳🇱 __**Example:**__
    ```ini\n[1] dec!dutch hebben\n[2] dec!nl leren\n[3] dec!dutch verlaten\n[4] dec!nl horen"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://www.mijnwoordenboek.nl/werkwoord/{temp_verb.lower()}'
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
  @commands.cooldown(1, 5, commands.BucketType.user)
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

    root = f'https://conjugator.reverso.net/conjugation-japanese-verb-{temp_verb.lower()}.html'
    emoji_title = '🇯🇵'
    return await self.__conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Japanese', space=True, aligned=False)

  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.command(aliases=['sa', 'ar'])
  async def arabic(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Arabic.\n:param verb: The verb to conjugate.```
    
    🇸🇦-🇪🇬 __**Example:**__
    ```ini\n[1] dec!arabic عمل\n[2] dec!sa Hakama\n[3] dec!ar ʾakhadha\n[4] dec!arabic فَعَلَ"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-arabic-verb-{temp_verb.lower()}.html'
    emoji_title = '🇸🇦-🇪🇬'
    return await self.__conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Arabic', space=True, aligned=False)

  @commands.command(aliases=['pt', 'portugais', 'portugués', 'português'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def portuguese(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Portuguese.\n:param verb: The verb to conjugate.```
    
    🇧🇷-🇵🇹 __**Example:**__
    ```ini\n[1] dec!portuguese ser\n[2] dec!pt estar\n[3] dec!portugais ir\n[4] dec!portugués fazer"""

    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb.lower()}.html'
    emoji_title = '🇧🇷-🇵🇹'
    language_title = 'Portuguese'
    return await self.__conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title=language_title, space=True)

  @commands.command(aliases=['it', 'italiano', 'italien', 'ita'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def italian(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Italian.\n:param verb: The verb to conjugate.```
    
    🇮🇹-🇨🇭 __**Example:**__
    ```ini\n[1] dec!italian trovare\n[2] dec!it essere\n[3] dec!italiano avere\n[4] dec!italien finire"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-italian-verb-{temp_verb.lower()}.html'
    emoji_title = '🇮🇹-🇨🇭'
    return await self.__conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Italian')

  @commands.command(aliases=['fr', 'français', 'francés', 'francais', 'francês', 'frances'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def french(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in French.\n:param verb: The verb to conjugate.```
    
    🇫🇷-🇧🇪 __**Example:**__
    ```ini\n[1] dec!french être\n[2] dec!fr avoir\n[3] dec!français faire\n[4] dec!francés lire"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-french-verb-{temp_verb.lower()}.html'
    emoji_title = '🇫🇷-🇧🇪'
    return await self.__conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='French')
  
  @commands.command(aliases=['es', 'español', 'espanhol', 'espagnol', 'espanol'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def spanish(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Spanish.\n:param verb: The verb to conjugate.```
    
    🇪🇸-🇲🇽 __**Example:**__
    ```ini\n[1] dec!spanish hacer\n[2] dec!es tener\n[3] dec!español estoy\n[4] dec!espagnol stoy"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-spanish-verb-{temp_verb.lower()}.html'

    emoji_title = '🇪🇸-🇲🇽'
    return await self.__conjugate(ctx=ctx, root=root, 
  verb=verb, emoji_title=emoji_title, language_title='Spanish')

  @commands.command(aliases=['en', 'eng', 'ing', 'inglés', 'ingles'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def english(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in English.\n:param verb: The verb to conjugate.```
    
    🇺🇸-🇬🇧 __**Example:**__
    ```ini\n[1] dec!english make\n[2] dec!en to do\n[3] dec!eng get\n[4] dec!inglés to guess"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-english-verb-{temp_verb.lower()}.html'
    emoji_title = "🇺🇸-🇬🇧"
    return await self.__conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='English')

  async def __conjugate(self, ctx, root: str, verb: str, emoji_title: str, language_title: str, space: bool = False, aligned: bool = True) -> None:
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
        title=f"{emoji_title} Conjugation",
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

      
      verbal_mode = ''

      conjugations = {}
      for i, current_row in enumerate(word_wrap_rows):
        conjugations[f'page{i}'] = []

        # Loops through the rows
        for table in current_row.select('.wrap-three-col'):
          # Specifies the verbal tense if there is one
          if temp_tense_name := table.select_one('p'):
            tense_name = temp_tense_name.get_text()

            # Changes verbal mode if it's time to change it
            if (temp_title := table.select_one('.word-wrap-title')):
              title = temp_title.get_text().strip()
              verbal_mode = title
            elif (temp_title := current_row.select_one('.word-wrap-title')):
              title = temp_title.get_text().strip()
              verbal_mode = title

            verbal_mode = title

          # If there isn't, it shows '...' instead
          else:
            tense_name = '...'
            verbal_mode = table.select_one('.word-wrap-title').get_text().strip()

          temp_text = ""

          # Loops through each tense row
          for li in table.select('.wrap-verbs-listing li'):
            # Makes a temp text with all conjugations
            if space:
              temp_text += f"{li.get_text(separator=' ')}\n"
            else:
              temp_text += f"{li.get_text()}\n"
          # Specifies the verbal mode
          temp_text += f"""\nmode="{verbal_mode}"\n"""
          temp_text = f"```apache\n{temp_text}```"
          conjugations[f'page{i}'].append({'tense': [temp_text, tense_name, aligned]})

      index = 0
      # Sends initial embed and adds the arrow emojis to it
      msg = await ctx.send(embed=discord.Embed(
        title=emoji_title))
      await msg.add_reaction('⬅️')
      await msg.add_reaction('➡️')
      await asyncio.sleep(0.5)

      while True:
        embed.title = f"{language_title} Conjugation ({index+1}/{len(conjugations)})"
        embed.clear_fields()
        the_key = list(conjugations.keys())[index]
        for a_dict in conjugations[the_key]:
          for page, values in dict(a_dict).items():
            embed.add_field(
              name=values[1],
              value=values[0],
              inline=values[2]
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
            if index < len(conjugations) - 1:
              index += 1
            await msg.remove_reaction(r, u)
            continue

  @conjugate.command(aliases=['de', 'deutsch', 'ger'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def german(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in German.\n:param verb: The verb to conjugate.```
    
    🇩🇪|🇦🇹 __**Example:**__
    ```ini\n[1] dec!conj german habben\n[2] dec!conj deutsch gehen\n[3] dec!conj de sprachen\n[4] dec!conj ger essen"""
    if not verb:
      return await ctx.send("**Please, type a word**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://conjugator.reverso.net/conjugation-german-verb-{temp_verb.lower()}.html'
    emoji_title = '🇩🇪|🇦🇹'
    return await self.__conjugate(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='German')

  async def __cooljugator(self, ctx, root: str, verb: str, emoji_title: str, language_title: str, space: bool = False, aligned: bool = True) -> None:
    """ Conjugates a verb using the Cooljugator website. 
    :param root: The url to make the GET request from.
    :param verb: The verb to conjugate.
    :param emoji_title: The emoji to show in the embeds.
    :param language_title: The language that is being conjugated.
    :param space: If you want a space separator into a specific section. 
    :param aligned: If the fields will be inline."""


    # Performs the GET request to the endpoint
    async with self.session.get(root) as response:
      if response.status != 200:
        return await ctx.send("**Something went wrong with that search!**")

      # Gets the html and the container div
      html = BeautifulSoup(await response.read(), 'html.parser')
      container = html.select_one('#conjugationDivs.fourteen.wide.column')
      if not container:
        return await ctx.send("**Couldn't find anything for it!**")

      
      title = html.select_one('#conjugation-data.ui.segment > .centered > h1').get_text().strip()

      conjugations = []
      conj_divs = container.select('.conjugation-table.collapsable')
      # Makes initial embed
      embed = discord.Embed(
        description=title,
        color=ctx.author.color,
        timestamp=ctx.message.created_at,
        url=root
      )
      # Gets all useful information
      for i, conj_div in enumerate(conj_divs):
        # Gets all pronouns
        pronouns = [
          pronoun.get_text(separator=' ').strip()
          for pronoun in conj_div.select(
            '.conjugation-cell.conjugation-cell-four.conjugation-cell-pronouns.pronounColumn'
          ) if pronoun.get_text()
        ]
        # Gets all tenses
        tenses = [
          tense.get_text().strip() 
          for tense in conj_div.select(
            '.conjugation-cell.conjugation-cell-four.tense-title'
          ) if tense.get_text()
        ]
        # Gets all conjugations
        conjs = [
          conj.get_text(separator='  ').strip() if conj.get_text() else '' 
          for conj in conj_div.select(
            '.conjugation-cell.conjugation-cell-four'
          )
        ][1:]
        # Filters the conjugations a bit
        new_conjs = []
        for conj in conjs:
          if conj.strip() not in pronouns and conj.strip() not in tenses:
            conj = conj.strip().split('  ')[0]
            new_conjs.append(conj)

        # Unify the pronouns with the conjugations
        rows = []
        pronouns = cycle(pronouns)
        for conj in new_conjs:
          if conj:
            try:
              temp = f"{next(pronouns)} {conj}"
            except Exception as e:
              temp = f"- {conj}"

            rows.append(temp)
        
        # Unify the tenses with the rows
        n = round(len(rows)/len(tenses))
        rows = [rows[i:i + n] for i in range(0, len(rows), n)]
        pairs = list(zip_longest(tenses, rows, fillvalue='_'))
        conjugations.append(pairs)

    # Initial index
    index = 0
    # Sends initial msg
    msg = await ctx.send(embed=discord.Embed(title=emoji_title))
    await asyncio.sleep(0.5)
    await msg.add_reaction('⬅️')
    await msg.add_reaction('➡️')
    # Main loop for switching pages
    while True:
      current = conjugations[index]
      embed.clear_fields()
      embed.title = f"{language_title} conjugation ({index+1}/{len(conjugations)})"
      # Adds a field for each conjugation table of the current tense
      for conj in current:
        temp_text = '\n'.join(conj[1])
        embed.add_field(
          name=conj[0],
          value=f"```apache\n{temp_text}```\n",
          inline=True
        )
      # Updates the embedded message
      await msg.edit(embed=embed)
      # Waits for user reaction in order to switch pages
      try:
        r, u = await self.client.wait_for(
          'reaction_add',
          timeout=60,
          check=lambda r, u: r.message.id == msg.id and u.id == ctx.author.id and \
          str(r.emoji) in ['⬅️', '➡️']
        )
      except asyncio.TimeoutError:
        await msg.remove_reaction('➡️', self.client.user)
        await msg.remove_reaction('⬅️', self.client.user)
        break
      else:
        if str(r.emoji) == '➡️':
          await msg.remove_reaction('➡️', u)
          if index < len(conjugations) - 1:
            index += 1
          continue
        else:
          await msg.remove_reaction('⬅️', u)
          if index > 0:
            index -= 1
          continue

  @conjugate.command(aliases=['po', 'pl', 'polski', 'polonais', 'polonês', 'polonés'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def polish(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Polish.\n:param verb: The verb to conjugate.```
    
    🇵🇱 __**Example:**__
    ```ini\n[1] dec!conj polish dać\n[2] dec!conj po sprzedawać\n[3] dec!conj polski mówić\n[4] dec!conj pl jechać"""
    if not verb:
      return await ctx.send("**Please, type a verb**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root = f'https://cooljugator.com/pl/{temp_verb.lower()}'
    emoji_title = '🇵🇱'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Polish', space=True)
  
  @commands.command(aliases=['esp'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def esperanto(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Esperanto.\n:param verb: The verb to conjugate.```
    
    🟩 __**Example:**__
    ```ini\n[1] dec!esperanto esti\n[2] dec!esp povi\n[3] dec!esperanto havi\n[4] dec!esp fari"""
    if not verb:
      return await ctx.send("**Please, type a verb**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    # root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
    root =f'https://cooljugator.com/eo/{temp_verb.lower()}'

    emoji_title = '🟩'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Esperanto', space=True)

  @commands.command(aliases=['ee'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def estonian(self, ctx, *, verb: str = None) -> None:
    """Conjugates a verb in Estonian.\n:param verb: The verb to conjugate.```
    
    🇪🇪 __**Example:**__
    ```ini\n[1] dec!estonian olema\n[2] dec!ee tootma\n[3] dec!estonian jätkuma\n[4] dec!ee tõmbuma"""
    if not verb:
      return await ctx.send("**Please, type a verb**")

    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    # root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
    root =f'https://cooljugator.com/ee/{temp_verb.lower()}'

    emoji_title = '🇪🇪'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Estonian', space=True)

  @commands.command(aliases=['tr'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def turkish(self, ctx, verb: str = None) -> None:
    """Conjugates a verb in Turkish.\n:param verb: The verb to conjugate.```
    
    🇹🇷 __**Example:**__
    ```ini\n[1] dec!turkish edilmek\n[2] dec!tr bilmek\n[3] dec!turkish söylemek\n[4] dec!tr etmek"""
    if not verb:
      return await ctx.send("**Please, type a verb**")


    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value,I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    # root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
    root =f'https://cooljugator.com/tr/{temp_verb.lower()}'

    emoji_title = '🇹🇷'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Turkish', space=True)

  @commands.command(aliases=['dk', 'dansk'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def danish(self, ctx, verb: str = None) -> None:
    """Conjugates a verb in Danish.\n:param verb: The verb to conjugate.```
    
    🇩🇰 __**Example:**__
    ```ini\n[1] dec!danish ske\n[2] dec!dansk have\n[3] dec!dk gå\n[4] dec!danish fortælle"""
    if not verb:
      return await ctx.send("**Please, type a verb**")


    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value, I'm not using it!**")

    temp_verb = '%20'.join(verb.split())

    root =f'https://cooljugator.com/da/{temp_verb.lower()}'

    emoji_title = '🇩🇰'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Danish', space=True)

  @commands.command(aliases=['se', 'svensk'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def swedish(self, ctx, verb: str = None) -> None:
    """Conjugates a verb in Swedish.\n:param verb: The verb to conjugate.```
    
    🇸🇪 __**Example:**__
    ```ini\n[1] dec!swedish ha\n[2] dec!se framhärda\n[3] dec!svensk finna\n[4] dec!swedish försvåra"""
    if not verb:
      return await ctx.send("**Please, type a verb**")


    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value, I'm not using it!**")

    temp_verb = '%20'.join(verb.split())
    
    root =f'https://cooljugator.com/sv/{temp_verb.lower()}'

    emoji_title = '🇸🇪'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Swedish', space=True)

  @commands.command(aliases=['no', 'norsk'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def norwegian(self, ctx, verb: str = None) -> None:
    """Conjugates a verb in Norwegian.\n:param verb: The verb to conjugate.```
    
    🇳🇴 __**Example:**__
    ```ini\n[1] dec!norwegian være\n[2] dec!no have\n[3] dec!norsk si\n[4] dec!norwegian få"""
    if not verb:
      return await ctx.send("**Please, type a verb**")


    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value, I'm not using it!**")

    temp_verb = '%20'.join(verb.split())
    
    root =f'https://cooljugator.com/no/{temp_verb.lower()}'

    emoji_title = '🇳🇴'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Norwegian', space=True)


  @commands.command(aliases=['fo'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def faroese(self, ctx, verb: str = None) -> None:
    """Conjugates a verb in Faroese.\n:param verb: The verb to conjugate.```
    
    🇫🇴 __**Example:**__
    ```ini\n[1] dec!faroese tørva\n[2] dec!fo hjálpa\n[3] dec!fo steðga\n[4] dec!faroese læra"""
    if not verb:
      return await ctx.send("**Please, type a verb**")


    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value, I'm not using it!**")

    temp_verb = '%20'.join(verb.split())
    
    root =f'https://cooljugator.com/fo/{temp_verb.lower()}'

    emoji_title = '🇫🇴'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Faroese', space=True)

  @commands.command(aliases=['is'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def icelandic(self, ctx, verb: str = None) -> None:
    """Conjugates a verb in Icelandic.\n:param verb: The verb to conjugate.```
    
    🇮🇸 __**Example:**__
    ```ini\n[1] dec!icelandic kveða\n[2] dec!is þróa\n[3] dec!is bæsa\n[4] dec!icelandic rjúfa"""
    if not verb:
      return await ctx.send("**Please, type a verb**")


    if len(verb) > 50:
      return await ctx.send("**Wow, you informed a very long value, I'm not using it!**")

    temp_verb = '%20'.join(verb.split())
    
    root =f'https://cooljugator.com/is/{temp_verb.lower()}'

    emoji_title = '🇮🇸'
    return await self.__cooljugator(ctx=ctx, root=root, 
    verb=verb, emoji_title=emoji_title, language_title='Icelandic', space=True)

def setup(client) -> None:
  client.add_cog(Conjugation(client))