import discord
from discord.ext import commands
from discord import ApplicationContext, Option, option, SlashCommandGroup, slash_command

import aiohttp
import requests
import json
from bs4 import BeautifulSoup
import os

from typing import Any, List, Dict, Union
from others import utils
from others.views import PaginatorView

IS_LOCAL = utils.is_local()
TEST_GUILDS = [os.getenv("TEST_GUILD_ID")] if IS_LOCAL else None


class Dictionaries(commands.Cog):
	""" A category for word dictionaries. """

	def __init__(self, client) -> None:
		""" Class initializing method. """

		self.client = client
		self.session = aiohttp.ClientSession(loop=client.loop)

	_dictionary = SlashCommandGroup("dictionary", "Searches something in the Cambridge dictionary", guild_ids=TEST_GUILDS)

	@commands.Cog.listener()
	async def on_ready(self) -> None:
		""" Tells when the cog is ready to use. """

		print("Dictionary cog is online")

	@_dictionary.command(name="english")
	@commands.cooldown(1, 10, commands.BucketType.user)
	@utils.check_command_limit()
	async def _dictionary_english(self, interaction, search: Option(str, name="search", description="What you want to search there.", required=True)) -> None:
		""" Searches something in the Cambridge dictionary. """

		member = interaction.author
		await interaction.defer(ephemeral=True)

		req = f"https://dictionary.cambridge.org/us/dictionary/english/{search.strip().replace(' ', '%20')}"
		async with self.session.get(req, headers={'User-Agent': 'Mozilla/5.0'}) as response:
			if response.status != 200:
				return await interaction.respond(f"**{member.mention}, something went wrong with that search!**", ephemeral=True)

			html = BeautifulSoup(await response.read(), 'html.parser')

			page = html.select_one('.page')

			if not page:
				return await interaction.respond(f"**{member.mention}, nothing found for the given search!**", ephemeral=True)
				
			examples = page.select('.pr .dictionary')


			# Additional data:
			additional = {
				'client': self.client,
				'req': req,
				'search': search,
				'change_embed': self.make_embed
			}
			view = PaginatorView(examples, **additional)
			embed = await view.make_embed(interaction.author)
			await interaction.respond(embed=embed, view=view)

	async def get_header(self, example) -> Dict[str, str]:
		""" Gets a header for the example. 
		:param example: The whole HTML of the search word example. """

		header = example.select_one('.pos-header')

		# Gets simple tags from the HTML, as the title, type of word (noun, adjective, verb, etc)
		title = header.select_one('.di-title').get_text().strip()
		kind = kd.get_text().strip() if (kd := header.select_one('.posgram.dpos-g.hdib.lmr-5')) else '?'

		# Gets all phonetic texts from elements that have specific class names in the list below
		phonetics = []
		for phonetic_tag in ['.us.dpron-i', '.uk.dpron-i']:
			if pho := header.select_one(phonetic_tag):
				temp_pho_span = []
				# Gets only text from useful subtags, as listed below
				for cl in [['region', 'dreg'], ['pron', 'dpron']]:
					for content in pho.contents:
						if content.get('class') == cl:
							# Appends to the a temp list, regarding this iteration
							temp_pho_span.append(content.get_text().strip())

				# Appends to the main list
				phonetics.append(' '.join(temp_pho_span[:]))

		# Makes a neat dictionary to return it and be easier to handle the data
		header_dict = {
			"title": title,
			"kind": kind,
			"phonetics": ' | '.join(phonetics) if phonetics else '?'
		}
		
		# Returns it
		return header_dict


	async def get_content(self, example) -> Any:
		""" Gets the content of the given search. 
		:param example: The whole HTML of the search word example. """

		# Gets the main example div
		content = example.select_one('.pos-body')
		# Gets the inner content of the main example div
		# inner = content.select_one('.hflxrev.hdf-xs.hdb-s.hdf-l')
		# Gets image, word level (a1, a2, b1, b2, c1, c2) and the description
		image_class = '.dimg > amp-img'
		image = f"https://dictionary.cambridge.org/{link['src']}" if (link := content.select_one(image_class)) else ''
		level = level.get_text().strip() if (level := content.select_one('.def-info.ddef-info')) else ''
		description = content.select_one('.def.ddef_d.db').get_text().strip()

		the_content = {
			'level': level,
			'description': description,
			'image': image
		}

		return the_content

	async def get_examples(self, example) -> List[Any]:
		""" Get examples for the given search. 
		:param example: The whole HTML of the search wor example. """

		# Gets the main examples div
		examples_div = example.select_one('.def-body.ddef_b')
		# Gets all examples
		examples = []
		if examples_div:
			examples = examples_div.select('.examp.dexamp')
			examples = list(map(lambda ex: ex.get_text().strip(), examples))

		return examples

	async def make_embed(self, req: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
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

		header = await self.get_header(example)
		current_time = await utils.get_time_now()

		# Makes the embed's header
		embed = discord.Embed(
			title=f"Search for __{search}__",
			description=f"**Title:** `{header['title']}`\n**Kind:** `{header['kind']}`\n**Phonetics:** `{header['phonetics']}`",
			color=member.color,
			timestamp=current_time,
			url=req
		)

		# Adds a content field with the search value description
		content = await self.get_content(example)
		# Adds a word level and an image if there is one, respectively
		embed.add_field(name=f"({content['level']})", value=content['description'], inline=False)
		embed.set_thumbnail(url=content['image'])
		examples = await self.get_examples(example)
		# Adds a field for each example
		for i, example in enumerate(examples):
			embed.add_field(name=f"Example {i+1}", value=f"```{example}```", inline=True)

		# Sets the author of the search
		embed.set_author(name=member, icon_url=member.display_avatar)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=member.guild.icon.url)

		return embed


	@_dictionary.command(name="french")
	@commands.cooldown(1, 10, commands.BucketType.user)
	@utils.check_command_limit()
	async def _dictionary_french(self, interaction, search: Option(str, name="search", description="The word you are looking for.", required=True)) -> None:
		""" Searches a word in a French dictionary. """

		member = interaction.author

		await interaction.defer(ephemeral=True)

		url = f"https://dicolink.p.rapidapi.com/mot/{search.strip().replace(' ', '%20')}/definitions"

		headers = {
			'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
			'x-rapidapi-host': "dicolink.p.rapidapi.com"
			}

		async with self.session.get(url=url, headers=headers) as response:
			if response.status != 200:
				return await interaction.respond(f"**Nothing found, {member.mention}!**", ephemeral=True)

			data = json.loads(await response.read())

			# Additional data:
			additional = {
				'client': self.client,
				'req': response,
				'search': search,
				'change_embed': self.make_french_embed
			}
			view = PaginatorView(data, **additional)
			embed = await view.make_embed(interaction.author)
			await interaction.respond(embed=embed, view=view)


	async def make_french_embed(self, req: str, member: Union[discord.Member, discord.User], search: str, example: Any, 
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

		# Makes the embed's header
		embed = discord.Embed(
			title="__French Dictionary__",
			description=f"Showing results for: {example['mot']}",
			color=member.color,
			timestamp=current_time,
			url=example['dicolinkUrl']
		)

		# General info
		embed.add_field(name="__Information__", inline=False,
			value=f"**Word:** {example['mot']} | **ID:** {example['id']}\n**Nature:** {example['nature']} | **Source:** [{example['source']}]({example['attributionUrl']})")

		# Adds a field for each example
		embed.add_field(name="__Definition__", value=example['definition'], inline=False)

		# Sets the author of the search
		embed.set_author(name=member, icon_url=member.display_avatar)
		# Makes a footer with the a current page and total page counter
		embed.set_footer(text=f"{offset}/{lentries}", icon_url=member.guild.icon.url)

		return embed


def setup(client) -> None:
	""" Cog's setup function. """

	client.add_cog(Dictionaries(client))