import discord
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
from discord_slash.model import ButtonStyle

class SwitchPages:
	""" A class for switching dictionary page. """

	def __init__(self, data, **kwargs):
		""" Class initializing method. """

		self.data = data
		self.client = kwargs.get('client')
		self.req = kwargs.get('req')
		self.search = kwargs.get('search')
		self.change_embed = kwargs.get('change_embed')

	async def start(self, interaction) -> None:


		action_row = create_actionrow(
			create_button(
					style=ButtonStyle.blurple, label="Previous", custom_id="left_button", emoji='⬅️'
			),
			create_button(
					style=ButtonStyle.blurple, label="Next", custom_id="right_button", emoji='➡️'
			)
		)

		
		button_ctx = None

		index = 0

		await interaction.defer(hidden=True)

		while True:

			embed = await self.change_embed(
				req=self.req, interaction=interaction, search=self.search, 
				example=self.data[index], offset=index+1, lentries=len(self.data)
			)

			if button_ctx is None:
				await interaction.send(embed=embed, components=[action_row], hidden=True)
			else:
				await button_ctx.edit_origin(embed=embed, components=[action_row])
			# Send a message with buttons
			# Wait for someone to click on them
			button_ctx = await wait_for_component(self.client, components=action_row)

			await button_ctx.defer(edit_origin=True)
			
			# Send what you received

			if button_ctx.custom_id == 'left_button':
				if index > 0:
					index -= 1
				continue
			elif button_ctx.custom_id == 'right_button':
				if index < len(self.data) - 1:
					index += 1
				continue
