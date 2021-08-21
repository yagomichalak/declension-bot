import re
import discord
from discord import message
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
from discord_slash.model import ButtonStyle

import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from itertools import zip_longest, cycle

TEST_GUILDS = [459195345419763713]


class Conjugation(commands.Cog):
	""" A category for conjugation commands. """

	def __init__(self, client) -> None:
		""" Init method of the conjugation class. """
		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)


	@commands.Cog.listener()
	async def on_ready(self):
		print('Conjugations cog is online!')

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="germanic",
		name="dutch",
		description="Conjugates a verb in Dutch",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def dutch(self, interaction, *, verb: str = None) -> None:
		
		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://www.mijnwoordenboek.nl/werkwoord/{temp_verb.lower()}'
		async with self.session.get(root) as response:
			if response.status != 200:
				return await interaction.send("**Something went wrong with that search!**")

		
			# Gets the html, the conjugation table div and table
			html = BeautifulSoup(await response.read(), 'html.parser')
			content_box = html.select_one('.content_box')
			table_rows = [row for row in content_box.select('table tr')[1:]]
			lenro = len(table_rows)
			if lenro == 0:
				return await interaction.send("**Nothing found for the informed value!**")

			# Creates the initial embed
			embed = discord.Embed(
				color=interaction.author.color,
				timestamp=interaction.created_at,
				url=root
			)
			
			index = 0

			action_row = create_actionrow(
					create_button(
							style=ButtonStyle.blurple, label="Previous", custom_id="left_button", emoji='⬅️'
					),
					create_button(
							style=ButtonStyle.blurple, label="Next", custom_id="right_button", emoji='➡️'
					)
			)

			button_ctx = None

			# Loops through each row of the conjugation tables
			while True:
				embed.title = f"Dutch Conjugation ({round(lenro/(lenro-index))}/{round(lenro/11)})"
				embed.clear_fields()
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


				if button_ctx is None:
					await interaction.send(embed=embed, components=[action_row], hidden=True)
					# Wait for someone to click on them
					button_ctx = await wait_for_component(self.client, components=action_row)
				else:
					await button_ctx.edit_origin(embed=embed, components=[action_row])
					# Wait for someone to click on them
					button_ctx = await wait_for_component(self.client, components=action_row, messages=button_ctx.origin_message_id)

				await button_ctx.defer(edit_origin=True)
					
				# Send what you received

				if button_ctx.custom_id == 'right_button':

					if index + 11 <= len(table_rows) / 2:
							index += 12
					continue
				elif button_ctx.custom_id == 'left_button':
					if index > 0:
							index -= 12
					continue
	
	# Conjugators based on Reverso's website
	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="asian",
		name="japanese",
		description="Conjugates a verb in Japanese",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def japanese(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-japanese-verb-{temp_verb.lower()}.html'
		emoji_title = '🇯🇵'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Japanese', space=True, aligned=False)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="other",
		name="arabic",
		description="Conjugates a verb in Arabic",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def arabic(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-arabic-verb-{temp_verb.lower()}.html'
		emoji_title = '🇸🇦-🇪🇬'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Arabic', space=True, aligned=False)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="romance",
		name="portuguese",
		description="Conjugates a verb in Portuguese",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def portuguese(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb.lower()}.html'
		emoji_title = '🇧🇷-🇵🇹'
		language_title = 'Portuguese'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title=language_title, space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="romance",
		name="italian",
		description="Conjugates a verb in Italian",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def italian(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-italian-verb-{temp_verb.lower()}.html'
		emoji_title = '🇮🇹-🇨🇭'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Italian')

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="romance",
		name="french",
		description="Conjugates a verb in French",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def french(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-french-verb-{temp_verb.lower()}.html'
		emoji_title = '🇫🇷-🇧🇪'
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='French')
	
	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="romance",
		name="spanish",
		description="Conjugates a verb in Spanish",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def spanish(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-spanish-verb-{temp_verb.lower()}.html'

		emoji_title = '🇪🇸-🇲🇽'
		return await self.__conjugate(interaction=interaction, root=root, 
	verb=verb, emoji_title=emoji_title, language_title='Spanish')

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="germanic",
		name="english",
		description="Conjugates a verb in English",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def english(self, interaction, verb: str) -> None:

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**", hidden=True)

		temp_verb = '%20'.join(verb.split())

		root = f'https://conjugator.reverso.net/conjugation-english-verb-{temp_verb.lower()}.html'
		emoji_title = "🇺🇸-🇬🇧"
		return await self.__conjugate(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='English')

	async def __conjugate(self, interaction, root: str, verb: str, emoji_title: str, language_title: str, space: bool = False, aligned: bool = True) -> None:
		""" Conjugates a verb.
		:param root: The language endpoint from which to do the HTTP request.
		:param verb: The verb that is being conjugated.
		"""

		await interaction.defer(hidden=True)

		async with self.session.get(root) as response:
			if response.status != 200:
				return await interaction.send("**Something went wrong with that search!**", ephemeral=True)

		
			# Gets the html and the table div
			html = BeautifulSoup(await response.read(), 'html.parser')
			subhead = html.select_one('.subHead.subHead-res.clearfix')
			if not subhead:
				return await interaction.send("**Invalid request!**", ephemeral=True)

			# Translation options
			#-> Word translation
			tr_div = subhead.select_one('.word-transl-options')
			found_verb = tr_div.select_one('.targetted-word-wrap').get_text().strip()

			embed = discord.Embed(
				title=f"{emoji_title} Conjugation",
				description=f"""**Searched:** {verb}
				**Found:** {found_verb}""",
				color=interaction.author.color,
				timestamp=interaction.created_at,
				url=root
			)
			embed.set_footer(
				text=f"Requested by {interaction.author}",
				icon_url=interaction.author.avatar_url)


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
			# Creates the Pagination buttons

			action_row = create_actionrow(
					create_button(
							style=ButtonStyle.blurple, label="Previous", custom_id="left_button", emoji='⬅️'
					),
					create_button(
							style=ButtonStyle.blurple, label="Next", custom_id="right_button", emoji='➡️'
					)
			)

			# Sends initial embed and adds the arrow emojis to it 

			button_ctx = None

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


				if button_ctx is None:
					await interaction.send(embed=embed, components=[action_row], hidden=True)
					# Wait for someone to click on them
					button_ctx = await wait_for_component(self.client, components=action_row)
				else:
					await button_ctx.edit_origin(embed=embed, components=[action_row])
					# Wait for someone to click on them
					button_ctx = await wait_for_component(self.client, components=action_row, messages=button_ctx.origin_message_id)

				await button_ctx.defer(edit_origin=True)
				
				# Send what you received

				if button_ctx.custom_id == 'left_button':
					if index > 0:
						index -= 1
					continue
				elif button_ctx.custom_id == 'right_button':
					if index < len(conjugations) - 1:
						index += 1
					continue

	@cog_ext.cog_subcommand(
	  base="conjugate",
	  subcommand_group="germanic",
	  name="german",
	  description="Conjugates a verb in German",
	  options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
	  ]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def german(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

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
				return await interaction.send("**Something went wrong with that search!**", ephemeral=True)

			# Gets the html and the container div
			html = BeautifulSoup(await response.read(), 'html.parser')
			container = html.select_one('#conjugationDivs.fourteen.wide.column')
			if not container:
				return await interaction.send("**Couldn't find anything for it!**", ephemeral=True)

			title = html.select_one('#conjugation-data.ui.segment > .centered > h1').get_text().strip()

			conjugations = []
			conj_divs = container.select('.conjugation-table.collapsable')
			# Makes initial embed
			embed = discord.Embed(
				description=title,
				color=interaction.author.color,
				timestamp=interaction.created_at,
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

		action_row = create_actionrow(
			create_button(
				style=ButtonStyle.blurple, label="Previous", custom_id="left_button", emoji='⬅️'
			),
			create_button(
				style=ButtonStyle.blurple, label="Next", custom_id="right_button", emoji='➡️'
			)
		)

		# Initial index and btn ctx
		index = 0
		button_ctx = None

		await interaction.defer(hidden=True)

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
			

			# Sends a message with buttons
			if button_ctx is None:
				await interaction.send(embed=embed, components=[action_row], hidden=True)
				# Wait for someone to click on them
				button_ctx = await wait_for_component(self.client, components=action_row)
			else:
				await button_ctx.edit_origin(embed=embed, components=[action_row])
				# Wait for someone to click on them
				button_ctx = await wait_for_component(self.client, components=action_row, messages=button_ctx.origin_message_id)

			await button_ctx.defer(edit_origin=True)

			if button_ctx.custom_id == 'right_button':
				if index < len(conjugations) - 1:
					index += 1
				continue
			elif button_ctx.custom_id == 'left_button':
				if index > 0:
					index -= 1
				continue

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="slavic",
		name="polish",
		description="Conjugates a verb in Polish",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def polish(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://cooljugator.com/pl/{temp_verb.lower()}'
		emoji_title = '🇵🇱'
		return await self.__cooljugator(interaction=interaction, root=root, 
			verb=verb, emoji_title=emoji_title, language_title='Polish', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="slavic",
		name="russian",
		description="Conjugates a verb in Russian",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def russian(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a word**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root = f'https://cooljugator.com/ru/{temp_verb}'
		emoji_title = '🇷🇺|🇧🇾'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Russian', space=True)


	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="romance",
		name="esperanto",
		description="Conjugates a verb in Esperanto",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def esperanto(self, interaction, *, verb: str = None) -> None:
		if not verb:
			return await interaction.send("**Please, type a verb**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		# root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
		root =f'https://cooljugator.com/eo/{temp_verb.lower()}'

		emoji_title = '🟩'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Esperanto', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="uralic",
		name="estonian",
		description="Conjugates a verb in Estonian",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def estonian(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")

		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		# root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
		root =f'https://cooljugator.com/ee/{temp_verb.lower()}'

		emoji_title = '🇪🇪'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Estonian', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="turkic",
		name="turkish",
		description="Conjugates a verb in Turkish",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def turkish(self, interaction, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value,I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		# root = f'https://conjugator.reverso.net/conjugation-portuguese-verb-{temp_verb}.html'
		root =f'https://cooljugator.com/tr/{temp_verb.lower()}'

		emoji_title = '🇹🇷'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Turkish', space=True)

	# North Germanic languages - Scandinavian languages
	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="germanic",
		name="danish",
		description="Conjugates a verb in Danish",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def danish(self, interaction, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())

		root =f'https://cooljugator.com/da/{temp_verb.lower()}'

		emoji_title = '🇩🇰'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Danish', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="germanic",
		name="swedish",
		description="Conjugates a verb in Swedish",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def swedish(self, interaction, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/sv/{temp_verb.lower()}'

		emoji_title = '🇸🇪'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Swedish', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="germanic",
		name="norwegian",
		description="Conjugates a verb in Norwegian",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def norwegian(self, interaction, verb: str = None) -> None:
		
		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/no/{temp_verb.lower()}'

		emoji_title = '🇳🇴'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Norwegian', space=True)


	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="germanic",
		name="faroese",
		description="Conjugates a verb in Faroese",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def faroese(self, interaction, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/fo/{temp_verb.lower()}'

		emoji_title = '🇫🇴'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Faroese', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="germanic",
		name="icelandic",
		description="Conjugates a verb in Icelandic",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def icelandic(self, interaction, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/is/{temp_verb.lower()}'

		emoji_title = '🇮🇸'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Icelandic', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="uralic",
		name="finnish",
		description="Conjugates a verb in Finnish",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def finnish(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/fi/{temp_verb.lower()}'

		emoji_title = '🇫🇮'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Finnish', space=True)


	# Asian languages
	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="asian",
		name="indonesian",
		description="Conjugates a verb in Indonesian",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def indonesian(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/id/{temp_verb.lower()}'

		emoji_title = '🇮🇩'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Indonesian', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="asian",
		name="maltese",
		description="Conjugates a verb in Maltese",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def maltese(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/mt/{temp_verb.lower()}'

		emoji_title = '🇲🇹'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Maltese', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="asian",
		name="thai",
		description="Conjugates a verb in Thai",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def thai(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/th/{temp_verb.lower()}'

		emoji_title = '🇹🇭'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Thai', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="asian",
		name="vietnamese",
		description="Conjugates a verb in Vietnamese",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def vietnamese(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/vi/{temp_verb.lower()}'

		emoji_title = '🇻🇳'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Vietnamese', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="asian",
		name="malay",
		description="Conjugates a verb in Malay",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def malay(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/ms/{temp_verb.lower()}'

		emoji_title = '🇲🇾'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Malay', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="romance",
		name="catalan",
		description="Conjugates a verb in Catalan",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def catalan(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/ca/{temp_verb.lower()}'

		emoji_title = '🟨'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Catalan', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="romance",
		name="romanian",
		description="Conjugates a verb in Romanian",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def romanian(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/ro/{temp_verb.lower()}'

		emoji_title = '🇷🇴'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Romanian', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="other",
		name="greek",
		description="Conjugates a verb in Greek",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def greek(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/gr/{temp_verb.lower()}'

		emoji_title = '🇬🇷'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Greek', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="germanic",
		name="afrikaans",
		description="Conjugates a verb in Afrikaans",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def afrikaans(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/af/{temp_verb.lower()}'

		emoji_title = '🇿🇦'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Afrikaans', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="uralic",
		name="lithuanian",
		description="Conjugates a verb in Lithuanian",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def lithuanian(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/lt/{temp_verb.lower()}'

		emoji_title = '🇱🇹'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Lithuanian', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="uralic",
		name="latvian",
		description="Conjugates a verb in Latvian",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def latvian(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/lv/{temp_verb.lower()}'

		emoji_title = '🇱🇻'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Latvian', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="slavic",
		name="macedonian",
		description="Conjugates a verb in Macedonian",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def macedonian(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/mk/{temp_verb.lower()}'

		emoji_title = '🇲🇰'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Macedonian', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="other",
		name="persian",
		description="Conjugates a verb in Persian",
		options=[
			create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def persian(self, interaction, verb: str) -> None:


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**", hidden=True)

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/fa/{temp_verb.lower()}'

		emoji_title = '🇮🇷'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Persian', space=True)

	@cog_ext.cog_subcommand(
		base="conjugate",
		subcommand_group="other",
		name="hebrew",
		description="Conjugates a verb in Hebrew",
		options=[
		create_option(name='verb', description='The word to conjugate', option_type=3, required=True)
		]#, guild_ids=TEST_GUILDS
	)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def hebrew(self, interaction, *, verb: str = None) -> None:

		if not verb:
			return await interaction.send("**Please, type a verb**")


		if len(verb) > 50:
			return await interaction.send("**Wow, you informed a very long value, I'm not using it!**")

		temp_verb = '%20'.join(verb.split())
		
		root =f'https://cooljugator.com/he/{temp_verb.lower()}'

		emoji_title = '🇮🇱'
		return await self.__cooljugator(interaction=interaction, root=root, 
		verb=verb, emoji_title=emoji_title, language_title='Hebrew', space=True)


def setup(client) -> None:
	client.add_cog(Conjugation(client))