import discord
from discord.ext import commands
from googletrans import Translator


class Tools(commands.Cog):
	""" A command for tool commands. """

	def __init__(self, client) -> None:
		""" Class initializing method. """

		self.client = client

	@commands.Cog.listener()
	async def on_ready(self) -> None:
		""" Tells when the cog is ready to use. """

		print('Tools cog is online!')


	@commands.command(aliases=['t', 'trans'])
	async def translate(self, ctx, language: str = None, *, message: str = None):
		""" Translates a message into another language.
		:param language: The language to translate the message to.
		:param message: The message to translate.
		:return: A translated message. """

		await ctx.message.delete()
		if not language:
			return await ctx.send("**Please, inform a language!**", delete_after=5)
		elif not message:
			return await ctx.send("**Please, inform a message to translate!**", delete_after=5)

		trans = Translator(service_urls=['translate.googleapis.com'])
		try:
			translation = trans.translate(f'{message}', dest=f'{language}')
		except ValueError:
			return await ctx.send("**Invalid parameter for 'language'!**", delete_after=5)
		embed = discord.Embed(title="__Translator__",
							  description=f"**Translated from `{translation.src}` to `{translation.dest}`**\n\n{translation.text}",
							  colour=ctx.author.color, timestamp=ctx.message.created_at)
		embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
		await ctx.send(embed=embed)


def setup(client) -> None:
	""" Cog's setup function. """

	client.add_cog(Tools(client))