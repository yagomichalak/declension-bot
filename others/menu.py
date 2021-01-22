import discord
from discord.ext import commands, menus


class SwitchPages(menus.ListPageSource):
	""" A class for switching dictionary page. """

	def __init__(self, data, **kwargs):
		""" Class initializing method. """

		super().__init__(data, per_page=1)
		self.req = kwargs.get('req')
		self.search = kwargs.get('search')
		self.change_embed = kwargs.get('change_embed')


	async def format_page(self, menu, entries):
		""" Formats each page. """

		offset = menu.current_page * self.per_page
		return await self.change_embed(
			req=self.req, ctx=menu.ctx, search=self.search, 
			example=entries, offset=offset+1, lentries=len(self.entries)
			)

