import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_permission
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
from discord_slash.model import ButtonStyle, SlashCommandPermissionType
import aiomysql
import os
from typing import Any, List, Dict, Union, Callable
import asyncio
from functools import reduce
from datetime import datetime
from others.customerrors import NotInWhitelist
from others import utils

TEST_GUILDS = [777886754761605140]

class FlashCard(commands.Cog, command_attrs=dict(hidden=False)):
  """ A category for creating, editing, deleting and showing 'FlashCard'. """

  def __init__(self, client) -> None:
    """Class initializing method."""

    self.client = client
    self.loop = asyncio.get_event_loop()
    self.whitelist: List[int] = []

  
  @commands.Cog.listener()
  async def on_ready(self) -> None:
    """ Tells when the cog is ready to use. """

    if await self.table_whitelist_exists():
      self.whitelist = await self.get_whitelist()
      
    print('FlashCard cog is online')

  # Discord commands

  def check_whitelist():
    async def real_check(interaction):
      if interaction.guild.id in interaction.command.cog.whitelist:
          return True
      raise NotInWhitelist("This server is not whitelisted!")
    return commands.check(real_check)


  @cog_ext.cog_subcommand(
		base="card", name="add",
		description="Adds a card into the database.", options=[
			create_option(name="front", description="The value for the front part of the card.", option_type=3, required=True),
			create_option(name="back", description="The value for the back part of the card.", option_type=3, required=True),
		]#, guild_ids=TEST_GUILDS
	)
  @commands.cooldown(1, 15, commands.BucketType.user)
  async def add_card(self, interaction, front: str, back: str) -> None:

    await interaction.defer(hidden=True)

    if not interaction.guild_id or interaction.guild.id not in self.whitelist:
      return await interaction.send("**This server is not whitelisted!**", hidden=True)

    member = interaction.author

    if len(front) > 300:
      return await interaction.send(f"**Length of the `front` parameter can't surpass 300 characters!**", hidden=True)

    if len(back) > 300:
      return await interaction.send(f"**Length of the `back` parameter can't surpass 300 characters!**", hidden=True)

    # Makes initial embed
    embed = discord.Embed(
      title="Do you want to confirm the values below?",
      color=member.color,
      timestamp=interaction.created_at
    )
    embed.set_footer(text="60 seconds to answer...")

    front = front.replace(r'\n', '\n')
    back = back.replace(r'\n', '\n')

    # Adds a field for the front and back side of the card
    embed.add_field(name="__Front__", value=f"```{front}```", inline=False)
    embed.add_field(name="__Back__", value=f"```{back}```", inline=False)

    # Asks user for confirmation of informed values
    action_row = create_actionrow(
        create_button(style=ButtonStyle.green, label="Confirm", custom_id="confirm_btn", emoji='✅'),
        create_button(style=ButtonStyle.red, label="Cancel", custom_id="cancel_btn", emoji='❌')
    )

    await interaction.send(embed=embed, components=[action_row], hidden=True)
    button_ctx = await wait_for_component(self.client, components=action_row)

    await button_ctx.defer(edit_origin=True)


    if button_ctx.custom_id == 'confirm_btn':
      the_time = await utils.get_timestamp()
      inserted = await self._insert_card(interaction.guild_id, member.id, front, back, the_time)
      if inserted:
        return await button_ctx.send("**Values confirmed! Added them into the DB...**", hidden=True)
      else:
        return await button_ctx.send("**Values confirmed! But this server is not whitelisted...**", hidden=True)
    elif button_ctx.custom_id == 'cancel_btn':
      return await button_ctx.send("**Values not confirmed! Not adding them into the DB...**", hidden=True)
	
  @cog_ext.cog_subcommand(
		base="card", name="delete",
		description="Deletes a card from the user's deck.", options=[
			create_option(name="card_id", description="The ID of the card that is gonna be deleted", option_type=4, required=True),
		]#, guild_ids=TEST_GUILDS
	)
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def delete_card(self, interaction, card_id: int) -> None:

    await interaction.defer(hidden=True)

    if not interaction.guild_id or interaction.guild_id not in self.whitelist:
      return await interaction.send("**This server is not whitelisted!**", hidden=True)

    member = interaction.author

    if not await self.card_exists(member.id, card_id):
      return await interaction.send(f"**You don't have a card with that ID, {member.mention}!**", hidden=True)

    await self._delete_card(member.id, card_id)
    await interaction.send(f"**Card with ID `{card_id}` was successfully deleted from your deck, {member.mention}!**", hidden=True)

  @cog_ext.cog_subcommand(
		base="card", name="list",
		description="Deletes a card from the user's deck."#, guild_ids=TEST_GUILDS
	)
  @commands.cooldown(1, 15, commands.BucketType.user)
  async def cards(self, interaction):
    """ Shows all cards of a particular user. """

    if not interaction.guild_id or interaction.guild_id not in self.whitelist:
      return await interaction.send("**This server is not whitelisted!**", hidden=True)

    member = interaction.author
    cards = await self.get_user_cards(member.id)
    return await self.pagination_looping(interaction, member, cards)

  @cog_ext.cog_subcommand(
		base="card", name="search",
		description="Searches for cards in the user's deck with the given search values.", options=[
			create_option(name="values", description="What is gonna be searched in the DB.", option_type=3, required=True),
		]#, guild_ids=TEST_GUILDS
	)
  @commands.cooldown(1, 15, commands.BucketType.user)
  async def search_cards(self, interaction, values: str) -> None:

    if not interaction.guild_id or interaction.guild_id not in self.whitelist:
      return await interaction.send("**This server is not whitelisted!**", hidden=True)

    member = interaction.author

    if len(values) > 300:
      return await interaction.send(f"Your search values have to be within 300 characters maximum, {member.mention}!**", hidden=True)

    if values := await self.fetch_values(member.id, values):
      return await self.pagination_looping(interaction, member, values)
    else:
      await interaction.send(f"**Nothing found with the given values, {member.mention}!**", hidden=True)


  async def pagination_looping(self, interaction: SlashContext, member: discord.Member, the_list: List[List[Any]]) -> None:
    """ Makes an infinite loop for paginating embedded messages. """

    embed = discord.Embed(
      description=f"**Total of cards:** {len(the_list)}",
      color=member.color,
      timestamp=interaction.created_at
    )

    index = 0
    button_ctx = None

    action_row = create_actionrow(
					create_button(
							style=ButtonStyle.blurple, label="Previous", custom_id="left_btn", emoji='⬅️'
					),
					create_button(
							style=ButtonStyle.blurple, label="Next", custom_id="right_btn", emoji='➡️'
					)
			)

    await interaction.defer(hidden=True)

    while True:
      # Clear current embed fields
      embed.clear_fields()
      embed.title=f"__{member}'s Cards__"
      embed.set_footer(text=f"{index+1}-{index+2} of {len(the_list)}")

      # Adds two fields to the embed
      for i in range(2):
        if len(the_list) <= index + i:
          break

        card = the_list[index + i]
        creation = datetime.utcfromtimestamp(card[4])
        
        embed.add_field(
          name=f"`@ Card - {index+i+1}` | `ID: {card[0]}`",
          value=f"```apache\nFront: {card[2]}\nBack: {card[3]}\n\n```**Created on: {creation}**",
          inline=False
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


      if button_ctx.custom_id == "right_btn":
        if index < (len(the_list) - 2):
          index += 2
        continue
      elif button_ctx.custom_id == "left_btn":
        if index > 0:
          index -= 2
        continue


  # Database methods

  @commands.is_owner()
  @commands.command(hidden=True)
  async def create_table(self, interaction) -> None:
    """ Creates the Cards table. """

    if await self.table_exists():
      return await interaction.send("**The __Cards__ table already exists!**", hidden=True)

    mycursor, db = await self.the_database()
    await mycursor.execute("""CREATE TABLE Cards (
      card_id BIGINT NOT NULL AUTO_INCREMENT,
      user_id BIGINT NOT NULL,
      front_value VARCHAR(300) NOT NULL,
      back_value VARCHAR(300) NOT NULL,
      timestamp BIGINT NOT NULL,
      PRIMARY KEY (card_id)
    ) DEFAULT CHARSET=utf8mb4""")
    await db.commit()
    await mycursor.close()
    await interaction.send("**Table __Cards__ created!**", hidden=True)

  @commands.command(hidden=True)
  @commands.is_owner()
  async def drop_table(self, interaction) -> None:
    """ Drops the Cards table. """

    if not await self.table_exists():
      return await interaction.send("**The __Cards__ table doesn't exist!**", hidden=True)

    mycursor, db = await self.the_database()
    await mycursor.execute("DROP TABLE Cards")
    await db.commit()
    await mycursor.close()
    await interaction.send("**Table __Cards__ dropped!**", hidden=True)

  @commands.command(hidden=True)
  @commands.is_owner()
  async def reset_table(self, interaction) -> None:
    """ Resets the Cards table. """

    if not await self.table_exists():
      return await interaction.send("**The __Cards__ table doesn't exist yet!**", hidden=True)

    mycursor, db = await self.the_database()
    await mycursor.execute("DELETE FROM Cards")
    await db.commit()
    await mycursor.close()
    await interaction.send("**Table __Cards__ reset!**", hidden=True)

  async def table_exists(self) -> bool:
    """ Gets all existing tables from the database. """

    mycursor, db = await self.the_database()
    await mycursor.execute("SHOW TABLE STATUS LIKE 'Cards'")
    table = await mycursor.fetchone()
    await mycursor.close()
    if table:
      return True
    else:
      return False

  async def _insert_card(self, server_id: int, user_id: int, front: str, back: str, timestamp: int) -> bool:
    """ Checks whether the Cards table exists. 
    :param server_id: The ID of the server which to check whether it's whitelisted.
    :param user_id: The ID of the card's creator.
    :param front: The value for the frontside of the card.
    :param back: The value for the backside of the card.
    :param timestamp: The creation timestamp.
    """

    if server_id in self.whitelist:
      mycursor, db = await self.the_database()
      await mycursor.execute("""INSERT INTO Cards (
        user_id, front_value, back_value, timestamp) 
        VALUES (%s, %s, %s, %s)""", (user_id, front, back, timestamp))
      await db.commit()
      await mycursor.close()
      return True
    else:
      return False

  async def _delete_card(self, user_id: int, card_id: int) -> None:
    """ Deletes a user card by ID. 
    :param user_id: The ID of the user from which the card is gonna be deleted.
    :param card_id: The ID of the card that is gonna be deleted. """

    mycursor, db = await self.the_database()
    await mycursor.execute("DELETE FROM Cards WHERE user_id = %s and card_id = %s", (user_id, card_id))
    await db.commit()
    await mycursor.close()

  async def get_user_cards(self, user_id: int) -> List[List[str]]:
    """ Gets all cards of a particular user.
    :param user_id: The ID of the user of which to get the cards. """

    mycursor, db = await self.the_database()
    await mycursor.execute("SELECT * FROM Cards WHERE user_id = %s", (user_id,))
    cards = await mycursor.fetchall()
    await mycursor.close()
    return cards

  async def fetch_values(self, user_id: int, values: str) -> List[List[str]]:
    """ Fetch cards from the user's deck with the given values. 
    :param user_id: The ID of the user from which the values are gonna be searched.
    :param values: The values for which are gonna be searched. """

    mycursor, db = await self.the_database()
    sql = "SELECT * FROM Cards WHERE user_id = " + str(user_id) + " AND front_value like '%" + \
    values + "%' OR back_value like '%" + values + "%'"
    await mycursor.execute(sql)
    found_values =  await mycursor.fetchall()
    await mycursor.close()
    return found_values

  async def card_exists(self, user_id: int, card_id: int) -> bool:
    """ Checks whether a user has a card.
    :param user_id: The ID of the user which it is gonna check.
    :param card_id: The ID of the card which it is gonna check.
    """

    mycursor, db = await self.the_database()
    await mycursor.execute("SELECT card_id FROM Cards WHERE user_id = %s and card_id = %s", (user_id, card_id))
    card_exists = await mycursor.fetchone()
    await mycursor.close()
    if card_exists:
      return True
    else:
      return False

  # Whitelist
  @cog_ext.cog_slash(
    name="addserver", description="Adds a server into the whitelist.", options=[
			create_option(name="server_id", description="The ID of the server to whitelist.", option_type=3, required=True),
		]#, guild_ids=TEST_GUILDS
    , default_permission=False, permissions={
      TEST_GUILDS[0]: [create_permission(647452832852869120, SlashCommandPermissionType.USER, True)]})
  async def insert_server(self, interaction, server_id: str) -> None:


    member = interaction.author
    if not server_id.isdigit():
      return await interaction.send(f"**Please, inform a server ID, {member.mention}!**", hidden=True)

    server_id = int(server_id)

    try:
      await self._insert_server(server_id)
      await interaction.send(f"**The informed server is now whitelisted, {member.mention}!**", hidden=True)
      self.whitelist.append(server_id)
    except Exception as e:
      print(e)
      await interaction.send(f"**It looks like this server was already whitelisted!**", hidden=True)


  @cog_ext.cog_slash(
    name="removeserver", description="Adds a server into the whitelist.", options=[
			create_option(name="server_id", description="The ID of the server to whitelist.", option_type=3, required=True),
		]#, guild_ids=TEST_GUILDS
    , default_permission=False, permissions={
      TEST_GUILDS[0]: [create_permission(647452832852869120, SlashCommandPermissionType.USER, True)]})
  async def delete_server(self, interaction, server_id: str) -> None:

    member = interaction.author
    if not server_id.isdigit():
      return await interaction.send(f"**Please, inform a server ID, {member.mention}!**", hidden=True)

    server_id = int(server_id)

    await self._delete_server(server_id)
    try:
      self.whitelist.remove(server_id)
    except:
      pass
    await interaction.send(f"**The informed server was removed from the whitelist, {member.mention}!**", hidden=True)

  @commands.command(hidden=True)
  @commands.is_owner()
  async def create_table_whitelist(self, interaction) -> None:
    """ Creates the Whitelist table. """

    if await self.table_whitelist_exists():
      return await interaction.send("**The __Whitelist__ table already exists!**", hidden=True)

    mycursor, db = await self.the_database()
    await mycursor.execute("""CREATE TABLE Whitelist (
      server_id BIGINT NOT NULL,
      PRIMARY KEY (server_id)
    ) DEFAULT CHARSET=utf8mb4""")
    await db.commit()
    await mycursor.close()
    await interaction.send("**Table __Whitelist__ created!**", hidden=True)

  @commands.command(hidden=True)
  @commands.is_owner()
  async def drop_table_whitelist(self, interaction) -> None:
    """ Drops the Whitelist table. """

    if not await self.table_whitelist_exists():
      return await interaction.send("**The __Whitelist__ table doesn't exist!**", hidden=True)

    mycursor, db = await self.the_database()
    await mycursor.execute("DROP TABLE Whitelist")
    await db.commit()
    await mycursor.close()
    await interaction.send("**Table __Whitelist__ dropped!**", hidden=True)

  @commands.command(hidden=True)
  @commands.is_owner()
  async def reset_table_whitelist(self, interaction) -> None:
    """ Resets the Cards table. """

    if not await self.table_whitelist_exists():
      return await interaction.send("**The __Whitelist__ table doesn't exist yet!**", hidden=True)

    mycursor, db = await self.the_database()
    await mycursor.execute("DELETE FROM Whitelist")
    await db.commit()
    await mycursor.close()
    await interaction.send("**Table __Whitelist__ reset!**", hidden=True)

  async def table_whitelist_exists(self) -> bool:
    """ Checks whether the table Whitelist exists. """

    mycursor, db = await self.the_database()
    await mycursor.execute("SHOW TABLE STATUS LIKE 'Whitelist'")
    table = await mycursor.fetchone()
    await mycursor.close()
    if table:
      return True
    else:
      return False

  async def _insert_server(self, server_id: int) -> None:
    """ Inserts a server into the whitelist. 
    :param server_id: The ID of the server which to insert into the whitelist. """

    mycursor, db = await self.the_database()
    await mycursor.execute("INSERT INTO Whitelist (server_id) VALUES (%s)", (server_id,))
    await db.commit()
    await mycursor.close()
    return True

  async def _delete_server(self, server_id: int) -> None:
    """ Deletes a server from the whitelist. 
    :param server_id: The ID of the server which to delete from the whitelist. """

    mycursor, db = await self.the_database()
    await mycursor.execute("DELETE FROM Whitelist WHERE server_id = %s", (server_id,))
    await db.commit()
    await mycursor.close()

  async def get_whitelist(self) -> List[int]:
    """ Gets all existing servers that are in the whitelist. """

    mycursor, db = await self.the_database()
    await mycursor.execute("SELECT server_id FROM Whitelist")
    whitelist = [s[0] for s in await mycursor.fetchall()]
    await mycursor.close()
    
    return whitelist

  async def the_database(self) -> List[Any]:
    """ Gets a database connection. """

    con = await aiomysql.create_pool(
      host=os.getenv("DB_HOST"),
      user=os.getenv("DB_USER"),
      password=os.getenv("DB_PASSWORD"),
      db=os.getenv("DB_NAME"),
      loop=self.loop
    )
    db = await con.acquire()
    mycursor = await db.cursor()
    return mycursor, db

def setup(client) -> None:
  """ Cog's setup function. """

  client.add_cog(FlashCard(client))