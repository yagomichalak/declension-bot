import discord
from discord.ext import commands
from discord import SlashCommandGroup, Option, ApplicationContext

import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from itertools import zip_longest, cycle

from others.views import PaginatorView
from others import utils
from typing import Union, Any, Dict
from pprint import pprint
import os

IS_LOCAL = utils.is_local()
TEST_GUILDS = [os.getenv("TEST_GUILD_ID")] if IS_LOCAL else None


class Conjugation(commands.Cog):
	""" A category for conjugation commands. """

	def __init__(self, client) -> None:
		""" Init method of the conjugation class. """
		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)

	_conjugate = SlashCommandGroup("conjugate", "Conjugates a verb in a given language.", guild_ids=TEST_GUILDS)
	_germanic = _conjugate.create_subgroup("germanic", "Conjugates a verb in a germanic language.", guild_ids=TEST_GUILDS)
	_slavic = _conjugate.create_subgroup("slavic", "Conjugates a verb in a slavic language.", guild_ids=TEST_GUILDS)
	_asian = _conjugate.create_subgroup("asian", "Conjugates a verb in an asian language.", guild_ids=TEST_GUILDS)
	_romance = _conjugate.create_subgroup("romance", "Conjugates a verb in a romance language.", guild_ids=TEST_GUILDS)
	_turkic = _conjugate.create_subgroup("turkic", "Conjugates a verb in a turkic language.", guild_ids=TEST_GUILDS)
	_uralic = _conjugate.create_subgroup("uralic", "Conjugates a verb in a uralic language.", guild_ids=TEST_GUILDS)
	_other = _conjugate.create_subgroup("other", "Conjugates a verb in another language.", guild_ids=TEST_GUILDS)

	@commands.Cog.listener()
	async def on_ready(self):
		print('Conjugations cog is online!')

	@_germanic.command(name="dutch", guild_ids=TEST_GUILDS)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def _conjugate_germanic_dutch(self, interaction, 
		verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Dutch. """
		
		await interaction.defer(ephemeral=True)

		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://www.mijnwoordenboek.nl/werkwoord/{temp_verb.lower()}'
		async with self.session.get(root) as response:
			if response.status != 200:
				return await interaction.respond("**Something went wrong with that search!**", ephemeral=True)

		
			# Gets the html, the conjugation table div and table
			html = BeautifulSoup(await response.read(), 'html.parser')
			content_box = html.select_one('.content_box')
			table_rows = [row for row in content_box.select('table tr')[1:]]
			lenro = len(table_rows)
			if lenro == 0:
				return await interaction.respond("**Nothing found for the informed value!**", ephemeral=True)

			# Additional data:
			additional = {
				'client': self.client,
				'req': root,
				'search': verb,
				'result': verb,
				'title': 'Dutch',
				'change_embed': self.make_specific_embed
			}
			view = PaginatorView(table_rows, increment=12, **additional)
			embed = await view.make_embed(interaction.author)
			await interaction.respond(embed=embed, view=view)

	async def make_specific_embed(self, req: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
		offset: int, lentries: int, entries: Dict[str, Any], title: str = None, result: str = None) -> discord.Embed:
		""" Makes an embed for the current search example.
		:param req: The request URL link.
		:param member: The member who triggered the command.
		:param search: The search that was performed.
		:param example: The current search example.
		:param offset: The current page of the total entries.
		:param lentries: The length of entries for the given search.
		:param title: The title of the search.
		:param result: The result of the search. """

		current_time = await utils.get_time_now()

		# Makes the embed's header
		embed = discord.Embed(
			title=f"Search for __{search}__",
			description=f"Dutch Conjugation",
			color=member.color,
			timestamp=current_time,
			url=req
			)

		embed.clear_fields()
		for i in range(0, 12, 2):
			if offset + i + 1< lentries:
				tense_name = entries[offset+i].get_text().strip()
				conjugation = entries[offset+i+1].get_text().strip().split('  ')
				conjugation = '\n'.join(conjugation)
			else:
				break

			# Adds a field for each table
			embed.add_field(
				name=tense_name,
				value=f"```apache\n{conjugation}```",
				inline=True
			)

		# Sets the author of the search
		embed.set_author(name=member, icon_url=member.display_avatar)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=member.guild.icon.url)
		return embed
	
	# Conjugators based on Reverso's website
	@_asian.command(name="japanese")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def japanese(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Japanese. """

		await interaction.defer(ephemeral=True)

		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-japanese-verb-{temp_verb.lower()}.html'
		emoji_title = '🇯🇵'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Japanese', space=True, aligned=False)

	@_other.command(name="arabic")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def arabic(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Arabic. """ 
		await interaction.defer(ephemeral=True)
		
		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-arabic-verb-{temp_verb.lower()}.html'
		emoji_title = '🇸🇦-🇪🇬'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Arabic', space=True, aligned=False)

	@_romance.command(name="portuguese")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def portuguese(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Portuguese. """

		await interaction.defer(ephemeral=True)
		
		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb.lower()}.html'
		emoji_title = '🇧🇷-🇵🇹'
		language_title = 'Portuguese'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title=language_title, space=True)

	@_romance.command(name="italian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def italian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Italian. """

		await interaction.defer(ephemeral=True)
		
		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-italian-verb-{temp_verb.lower()}.html'
		emoji_title = '🇮🇹-🇨🇭'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Italian')

	@_romance.command(name="french")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def french(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in French. """ 

		await interaction.defer(ephemeral=True)

		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-french-verb-{temp_verb.lower()}.html'
		emoji_title = '🇫🇷-🇧🇪'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='French')
	
	@_romance.command(name="spanish")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def spanish(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Spanish. """

		await interaction.defer(ephemeral=True)

		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-spanish-verb-{temp_verb.lower()}.html'

		emoji_title = '🇪🇸-🇲🇽'
		return await self.__conjugate(interaction=interaction, root=root, 
	verb=verb, emoji_title=emoji_title, language_title='Spanish')

	@_germanic.command(name="english")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def english(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in English. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-english-verb-{temp_verb.lower()}.html'
		emoji_title = "🇺🇸-🇬🇧"
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='English')

	async def __conjugate(self, interaction, root: str, verb: str, emoji_title: str, language_title: str, space: bool = False, aligned: bool = True) -> None:
		""" Conjugates a verb.
		:param root: The language endpoint from which to do the HTTP request.
		:param verb: The verb that is being conjugated. """

		current_time = await utils.get_time_now()
		async with self.session.get(root, headers={'User-Agent': 'Mozilla/5.0'}) as response:
			if response.status != 200:
				return await interaction.respond("**Something went wrong with that search!**", ephemeral=True)

		
			# Gets the html and the table div
			html = BeautifulSoup(await response.read(), 'html.parser')
			subhead = html.select_one('.subHead.subHead-res.clearfix')
			if not subhead:
				return await interaction.respond("**Invalid request!**", ephemeral=True)

		# Translation options
		#-> Word translation
		tr_div = subhead.select_one('.word-transl-options')
		found_verb = tr_div.select_one('.targetted-word-wrap').get_text().strip()
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

		# Additional data:
		additional = {
			'client': self.client,
			'req': root,
			'search': verb,
			'result': found_verb,
			'title': language_title,
			'change_embed': self.make_embed
		}
		view = PaginatorView(list(conjugations.items()), **additional)
		embed = await view.make_embed(interaction.author)
		await interaction.respond(embed=embed, view=view)
		return embed

	async def make_embed(self, req: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
		offset: int, lentries: int, entries: Dict[str, Any], title: str = None, result: str = None) -> discord.Embed:
		""" Makes an embed for the current search example.
		:param req: The request URL link.
		:param member: The member who triggered the command.
		:param search: The search that was performed.
		:param example: The current search example.
		:param offset: The current page of the total entries.
		:param lentries: The length of entries for the given search. """

		current_time = await utils.get_time_now()

		# Makes the embed's header
		embed = discord.Embed(
			title=f"{title} Conjugation ({offset}/{lentries})",
			description=f"""**Searched:** {search}
			**Found:** {result}""",
			color=member.color,
			timestamp=current_time,
			url=req
		)

		entries = dict(entries)

		the_key = list(entries.keys())[offset-1]
		for a_dict in entries[the_key]:
			for page, values in dict(a_dict).items():
				embed.add_field(
					name=values[1],
					value=values[0],
					inline=values[2])

		# Sets the author of the search
		embed.set_author(name=member, icon_url=member.display_avatar)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"Requested by {member}", icon_url=member.display_avatar)

		return embed

	async def make_cooljugator_embed(self, req: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
		offset: int, lentries: int, entries: Dict[str, Any], title: str = None, result: str = None) -> discord.Embed:
		""" Makes an embed for the current search example.
		:param req: The request URL link.
		:param member: The member who triggered the command.
		:param search: The search that was performed.
		:param example: The current search example.
		:param offset: The current page of the total entries.
		:param lentries: The length of entries for the given search. """

		current_time = await utils.get_time_now()

		# Makes the embed's header
		embed = discord.Embed(
			title=f"{title} Conjugation ({offset}/{lentries})",
			color=member.color,
			timestamp=current_time,
			url=req
		)

		current = entries[offset-1]
		# Adds a field for each conjugation table of the current tense
		for conj in current:
			temp_text = '\n'.join(conj[1])
			embed.add_field(
				name=conj[0],
				value=f"```apache\n{temp_text}```\n",
				inline=True
			)

		# Sets the author of the search
		embed.set_author(name=member, icon_url=member.display_avatar)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"Requested by {member}", icon_url=member.display_avatar)

		return embed

	@_germanic.command(name="german")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def german(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in German """

		await interaction.defer(ephemeral=True)
		
		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-german-verb-{temp_verb.lower()}.html'
		emoji_title = '🇩🇪|🇦🇹'
		return await self.__conjugate(interaction=interaction, root=root, 
			verb=verb, emoji_title=emoji_title, language_title='German')

	async def __cooljugator(self, interaction, root: str, verb: str, emoji_title: str, language_title: str, space: bool = False, aligned: bool = True) -> None:
		""" Conjugates a verb using the Cooljugator website. 
		:param root: The url to make the GET request from.
		:param verb: The verb to cog_ext.
		:param emoji_title: The emoji to show in the embeds.
		:param language_title: The language that is being conjugated.
		:param space: If you want a space separator into a specific section. 
		:param aligned: If the fields will be inline."""

		# Performs the GET request to the endpoint
		async with self.session.get(root) as response:
			if response.status != 200:
				return await interaction.respond("**Something went wrong with that search!**", ephemeral=True)

			# Gets the html and the container div
			html = BeautifulSoup(await response.read(), 'html.parser')
			container = html.select_one('#conjugationDivs.fourteen.wide.column')
			if not container:
				return await interaction.respond("**Couldn't find anything for it!**", ephemeral=True)

			title = html.select_one('#conjugation-data.ui.segment > .centered > h1').get_text().strip()

			conjugations = []
			conj_divs = container.select('.conjugation-table.collapsable')

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


		# Additional data:
		additional = {
			'client': self.client,
			'req': root,
			'search': verb,
			'result': verb,
			'title': language_title,
			'change_embed': self.make_cooljugator_embed
		}
		view = PaginatorView(conjugations, **additional)
		embed = await view.make_embed(interaction.author)
		await interaction.respond(embed=embed, view=view)
		return embed

	@_slavic.command(name="polish")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def polish(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Polish """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://cooljugator.com/pl/{temp_verb.lower()}'
		emoji_title = '🇵🇱'
		return await self.__cooljugator(interaction=interaction, root=root, 
			verb=verb, emoji_title=emoji_title, language_title='Polish', space=True)

	@_slavic.command(name="russian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def russian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Russian """

		await interaction.defer(ephemeral=True)

		if not verb:
			return await interaction.respond("**Please, type a word**", ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://cooljugator.com/ru/{temp_verb}'
		emoji_title = '🇷🇺|🇧🇾'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Russian', space=True)

	@_romance.command(name="esperanto")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def esperanto(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Esperanto """

		await interaction.defer(ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		# root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
		root =f'https://cooljugator.com/eo/{temp_verb.lower()}'

		emoji_title = '🟩'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Esperanto', space=True)

	@_uralic.command(name="estonian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def estonian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Estonian """

		await interaction.defer(ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		# root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
		root =f'https://cooljugator.com/ee/{temp_verb.lower()}'

		emoji_title = '🇪🇪'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Estonian', space=True)

	@_turkic.command(name="turkish")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def turkish(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Turkish """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value,I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		# root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
		root =f'https://cooljugator.com/tr/{temp_verb.lower()}'

		emoji_title = '🇹🇷'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Turkish', space=True)

	# North Germanic languages - Scandinavian languages
	@_germanic.command(name="danish")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def danish(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Danish" """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())

		root =f'https://cooljugator.com/da/{temp_verb.lower()}'

		emoji_title = '🇩🇰'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Danish', space=True)

	@_germanic.command(name="swedish")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def swedish(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Swedish" """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/sv/{temp_verb.lower()}'

		emoji_title = '🇸🇪'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Swedish', space=True)

	@_germanic.command(name="norwegian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def norwegian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Norwegian """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/no/{temp_verb.lower()}'

		emoji_title = '🇳🇴'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Norwegian', space=True)


	@_germanic.command(name="faroese")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def faroese(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Faroese" """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/fo/{temp_verb.lower()}'

		emoji_title = '🇫🇴'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Faroese', space=True)

	@_germanic.command(name="icelandic")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def icelandic(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Icelandic """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/is/{temp_verb.lower()}'

		emoji_title = '🇮🇸'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Icelandic', space=True)

	@_uralic.command(name="finnish")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def finnish(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Finnish """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/fi/{temp_verb.lower()}'

		emoji_title = '🇫🇮'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Finnish', space=True)

	# Asian languages
	@_asian.command(name="indonesian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def indonesian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Indonesian. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/id/{temp_verb.lower()}'

		emoji_title = '🇮🇩'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Indonesian', space=True)

	@_asian.command(name="maltese")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def maltese(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Maltese. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/mt/{temp_verb.lower()}'

		emoji_title = '🇲🇹'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Maltese', space=True)

	@_asian.command(name="thai")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def thai(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Thai. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/th/{temp_verb.lower()}'

		emoji_title = '🇹🇭'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Thai', space=True)

	@_asian.command(name="vietnamese")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def vietnamese(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Vietnamese. """

		await interaction.defer(ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/vi/{temp_verb.lower()}'

		emoji_title = '🇻🇳'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Vietnamese', space=True)

	@_asian.command(name="malay")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def malay(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Malay. """

		await interaction.defer(ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/ms/{temp_verb.lower()}'

		emoji_title = '🇲🇾'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Malay', space=True)

	@_romance.command(name="catalan")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def catalan(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Catalan. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/ca/{temp_verb.lower()}'

		emoji_title = '🟨'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Catalan', space=True)

	@_romance.command(name="romanian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def romanian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Romanian. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/ro/{temp_verb.lower()}'

		emoji_title = '🇷🇴'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Romanian', space=True)

	@_other.command(name="greek")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def greek(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Greek. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/gr/{temp_verb.lower()}'

		emoji_title = '🇬🇷'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Greek', space=True)

	@_germanic.command(name="afrikaans")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def afrikaans(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Afrikaans. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/af/{temp_verb.lower()}'

		emoji_title = '🇿🇦'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Afrikaans', space=True)

	@_uralic.command(name="lithuanian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def lithuanian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Lithuanian. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/lt/{temp_verb.lower()}'

		emoji_title = '🇱🇹'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Lithuanian', space=True)

	@_uralic.command(name="latvian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def latvian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Latvian. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/lv/{temp_verb.lower()}'

		emoji_title = '🇱🇻'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Latvian', space=True)

	@_slavic.command(name="macedonian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def macedonian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Macedonian. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/mk/{temp_verb.lower()}'

		emoji_title = '🇲🇰'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Macedonian', space=True)

	@_other.command(name="persian")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def persian(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Persian. """

		await interaction.defer(ephemeral=True)

		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/fa/{temp_verb.lower()}'

		emoji_title = '🇮🇷'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Persian', space=True)

	@_other.command(name="hebrew")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def hebrew(self, interaction, verb: Option(str, name='verb', description='The word to conjugate', required=True)) -> None:
		""" Conjugates a verb in Hebrew. """

		await interaction.defer(ephemeral=True)
		
		if len(verb) > 50:
			return await interaction.respond("**Wow, you informed a very long value, I'm not using it!**", ephemeral=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/he/{temp_verb.lower()}'

		emoji_title = '🇮🇱'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Hebrew', space=True)


def setup(client) -> None:
	client.add_cog(Conjugation(client))