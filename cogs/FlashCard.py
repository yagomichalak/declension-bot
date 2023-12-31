# Imports
import discord
from discord.ext import commands
from discord import Option, SlashCommandGroup, ApplicationContext, slash_command

import os
import asyncio
import aiomysql
from datetime import datetime
from typing import Any, List, Dict, Union

from others import utils
from others.views import PaginatorView
from others.prompt.menu import ConfirmButton
from others.customerrors import NotInWhitelist

# Environment variables
TEST_GUILDS = [777886754761605140]


class FlashCard(commands.Cog):
  """ A category for creating, editing, deleting and showing 'FlashCards'. """

  def __init__(self, client) -> None:
    """ Class initializing method."""

    self.client = client
    self.loop = asyncio.get_event_loop()
    self.whitelist: List[int] = []

  _card = SlashCommandGroup('card', 'FlashCard manager')#, guild_ids=TEST_GUILDS)
  
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

  @_card.command(name="add")
  @commands.cooldown(1, 15, commands.BucketType.user)
  async def _card_add(self, interaction, 
    front: Option(str, name="front", description="The value for the front part of the card.", required=True), 
    back: Option(str, name="back", description="The value for the back part of the card.", required=True)) -> None:
    """ Adds a card into the database. """

    await interaction.defer(ephemeral=True)

    if not interaction.guild_id or interaction.guild.id not in self.whitelist:
      return await interaction.respond("**This server is not whitelisted!**", ephemeral=True)

    member = interaction.author

    if len(front) > 300:
      return await interaction.respond(f"**Length of the `front` parameter can't surpass 300 characters!**", ephemeral=True)

    if len(back) > 300:
      return await interaction.respond(f"**Length of the `back` parameter can't surpass 300 characters!**", ephemeral=True)

    current_time = await utils.get_time_now()
    # Makes initial embed
    embed = discord.Embed(
      title="Do you want to confirm the values below?",
      color=member.color,
      timestamp=current_time
    )
    embed.set_footer(text="60 seconds to answer...")

    front = front.replace(r'\n', '\n')
    back = back.replace(r'\n', '\n')

    # Adds a field for the front and back side of the card
    embed.add_field(name="__Front__", value=f"```{front}```", inline=False)
    embed.add_field(name="__Back__", value=f"```{back}```", inline=False)

    # Asks user for confirmation of informed values
    
    confirm_view: discord.ui.View = ConfirmButton(member, timeout=120)

    msg = await interaction.respond(embed=embed, view=confirm_view, ephemeral=True)

    await confirm_view.wait()

    if confirm_view.value:
      the_time = await utils.get_timestamp()
      inserted = await self._insert_card(interaction.guild_id, member.id, front, back, the_time)
      if inserted:
        await confirm_view.interaction.followup.send("**Values confirmed! Added them into the DB...**", ephemeral=True)
      else:
        await confirm_view.interaction.followup.send("**Values confirmed! But this server is not whitelisted...**", ephemeral=True)
    elif confirm_view.value is False:
      await confirm_view.interaction.followup.send("**Values not confirmed! Not adding them into the DB...**", ephemeral=True)

    await utils.disable_buttons(confirm_view)
    await msg.edit(view=confirm_view)

  @_card.command(name="delete")
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def _card_delete(self, interaction, 
    card_id: Option(int, name="card_id", description="The ID of the card that is gonna be deleted", required=True)) -> None:
    """ Deletes a card from the user's deck. """

    await interaction.defer(ephemeral=True)

    if not interaction.guild_id or interaction.guild_id not in self.whitelist:
      return await interaction.respond("**This server is not whitelisted!**", ephemeral=True)

    member = interaction.author

    if not await self.card_exists(member.id, card_id):
      return await interaction.respond(f"**You don't have a card with that ID, {member.mention}!**", ephemeral=True)

    await self._delete_card(member.id, card_id)
    await interaction.respond(f"**Card with ID `{card_id}` was successfully deleted from your deck, {member.mention}!**", ephemeral=True)

  @_card.command(name="list")
  @commands.cooldown(1, 15, commands.BucketType.user)
  async def _card_list(self, interaction):
    """ Shows all cards of a particular user. """

    await interaction.defer(ephemeral=True)

    if not interaction.guild_id or interaction.guild_id not in self.whitelist:
      return await interaction.respond("**This server is not whitelisted!**", ephemeral=True)

    member = interaction.author
    cards = await self.get_user_cards(member.id)
    if not cards:
      return await interaction.respond("**No cards to show!**", ephemeral=True)

    await self.pagination_looping(interaction, member, cards)

  @_card.command(name="search")
  @commands.cooldown(1, 15, commands.BucketType.user)
  async def _card_search(self, interaction, 
    values: Option(str, name="values", description="What is gonna be searched in the DB.", required=True)) -> None:
    """ Searches for cards in the user's deck with the given search values. """

    await interaction.defer(ephemeral=True)

    if not interaction.guild_id or interaction.guild_id not in self.whitelist:
      return await interaction.respond("**This server is not whitelisted!**", ephemeral=True)

    member = interaction.author

    if len(values) > 300:
      return await interaction.respond(f"Your search values have to be within 300 characters maximum, {member.mention}!**", ephemeral=True)

    if values := await self.fetch_values(member.id, values):
      return await self.pagination_looping(interaction, member, values)
    else:
      await interaction.respond(f"**Nothing found with the given values, {member.mention}!**", ephemeral=True)

  async def pagination_looping(self, interaction: ApplicationContext, member: discord.Member, the_list: List[List[Any]]) -> None:
    """ Makes an infinite loop for paginating embedded messages. """

    # Additional data:
    additional = {
      'client': self.client,
      'change_embed': self.make_flashcard_embed
    }
    view = PaginatorView(the_list, increment=2, **additional)
    embed = await view.make_embed(interaction.author)
    await interaction.respond(embed=embed, view=view)

  async def make_flashcard_embed(self, 
      member: Union[discord.Member, discord.User], example: Any, offset: int, lentries: int, 
      entries: Dict[str, Any], req: str = None, search: str = None, title: str = None, result: str = None
    ) -> discord.Embed:

    current_time = await utils.get_time_now()

    embed = discord.Embed(
      title=f"__{member}'s Cards__",
      description=f"**Total of cards:** {lentries}",
      color=member.color,
      timestamp=current_time
    )

    embed.set_footer(text=f"{offset}-{offset+1} of {lentries}")

    # Adds two fields to the embed
    for i in range(2):
      if lentries <= offset - 1 + i:
        break

      card = entries[offset-1+i]
      creation = datetime.fromtimestamp(card[4])
      
      embed.add_field(
        name=f"`@ Card - {offset+i}` | `ID: {card[0]}`",
        value=f"```apache\nFront: {card[2]}\nBack: {card[3]}\n\n```**Created on: {creation}**",
        inline=False
      )

    return embed

  # Database methods

  @commands.is_owner()
  @commands.command(ephemeral=True)
  async def create_table(self, interaction) -> None:
    """ Creates the Cards table. """

    if await self.table_exists():
      return await interaction.respond("**The __Cards__ table already exists!**", ephemeral=True)

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
    await interaction.respond("**Table __Cards__ created!**", ephemeral=True)

  @commands.command(ephemeral=True)
  @commands.is_owner()
  async def drop_table(self, interaction) -> None:
    """ Drops the Cards table. """

    if not await self.table_exists():
      return await interaction.respond("**The __Cards__ table doesn't exist!**", ephemeral=True)

    mycursor, db = await self.the_database()
    await mycursor.execute("DROP TABLE Cards")
    await db.commit()
    await mycursor.close()
    await interaction.respond("**Table __Cards__ dropped!**", ephemeral=True)

  @commands.command(ephemeral=True)
  @commands.is_owner()
  async def reset_table(self, interaction) -> None:
    """ Resets the Cards table. """

    if not await self.table_exists():
      return await interaction.respond("**The __Cards__ table doesn't exist yet!**", ephemeral=True)

    mycursor, db = await self.the_database()
    await mycursor.execute("DELETE FROM Cards")
    await db.commit()
    await mycursor.close()
    await interaction.respond("**Table __Cards__ reset!**", ephemeral=True)

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

    if server_id not in self.whitelist:
      return False

    mycursor, db = await self.the_database()
    await mycursor.execute("""INSERT INTO Cards (
      user_id, front_value, back_value, timestamp) 
      VALUES (%s, %s, %s, %s)""", (user_id, front, back, timestamp))
    await db.commit()
    await mycursor.close()
    return True

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

    mycursor, _ = await self.the_database()
    await mycursor.execute("SELECT * FROM Cards WHERE user_id = %s", (user_id,))
    cards = await mycursor.fetchall()
    await mycursor.close()
    return cards

  async def fetch_values(self, user_id: int, values: str) -> List[List[str]]:
    """ Fetch cards from the user's deck with the given values. 
    :param user_id: The ID of the user from which the values are gonna be searched.
    :param values: The values for which are gonna be searched. """

    mycursor, _ = await self.the_database()
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

    mycursor, _ = await self.the_database()
    await mycursor.execute("SELECT card_id FROM Cards WHERE user_id = %s and card_id = %s", (user_id, card_id))
    card_exists = await mycursor.fetchone()
    await mycursor.close()
    if card_exists:
      return True
    else:
      return False

  # Whitelist
  @slash_command(name="addserver")#, guild_ids=TEST_GUILDS)
  @commands.is_owner()
  async def insert_server(self, interaction, 
    server_id: Option(str, name="server_id", description="The ID of the server to whitelist.", required=True)) -> None:
    """ Adds a server into the whitelist. """

    member = interaction.author
    if not server_id.isdigit():
      return await interaction.respond(f"**Please, inform a server ID, {member.mention}!**", ephemeral=True)

    server_id = int(server_id)

    try:
      await self._insert_server(server_id)
      await interaction.respond(f"**The informed server is now whitelisted, {member.mention}!**", ephemeral=True)
      self.whitelist.append(server_id)
    except Exception as e:
      print(e)
      await interaction.respond(f"**It looks like this server was already whitelisted!**", ephemeral=True)


  @slash_command(name="removeserver")#, guild_ids=TEST_GUILDS)
  @commands.is_owner()
  async def delete_server(self, interaction, 
    server_id: Option(str, name="server_id", description="The ID of the server to whitelist.", required=True)) -> None:
    """ Adds a server into the whitelist. """

    member = interaction.author
    if not server_id.isdigit():
      return await interaction.respond(f"**Please, inform a server ID, {member.mention}!**", ephemeral=True)

    server_id = int(server_id)

    await self._delete_server(server_id)
    try:
      self.whitelist.remove(server_id)
    except:
      pass
    await interaction.respond(f"**The informed server was removed from the whitelist, {member.mention}!**", ephemeral=True)

  @commands.command()
  @commands.is_owner()
  async def create_table_whitelist(self, ctx) -> None:
    """ Creates the Whitelist table. """

    if await self.table_whitelist_exists():
      return await ctx.send("**The __Whitelist__ table already exists!**")

    mycursor, db = await self.the_database()
    await mycursor.execute("""CREATE TABLE Whitelist (
      server_id BIGINT NOT NULL,
      PRIMARY KEY (server_id)
    ) DEFAULT CHARSET=utf8mb4""")
    await db.commit()
    await mycursor.close()
    await ctx.send("**Table __Whitelist__ created!**")

  @commands.command()
  @commands.is_owner()
  async def drop_table_whitelist(self, ctx) -> None:
    """ Drops the Whitelist table. """

    if not await self.table_whitelist_exists():
      return await ctx.send("**The __Whitelist__ table doesn't exist!**")

    mycursor, db = await self.the_database()
    await mycursor.execute("DROP TABLE Whitelist")
    await db.commit()
    await mycursor.close()
    await ctx.send("**Table __Whitelist__ dropped!**")

  @commands.command()
  @commands.is_owner()
  async def reset_table_whitelist(self, ctx) -> None:
    """ Resets the Cards table. """

    if not await self.table_whitelist_exists():
      return await ctx.send("**The __Whitelist__ table doesn't exist yet!**")

    mycursor, db = await self.the_database()
    await mycursor.execute("DELETE FROM Whitelist")
    await db.commit()
    await mycursor.close()
    await ctx.send("**Table __Whitelist__ reset!**")

  async def table_whitelist_exists(self) -> bool:
    """ Checks whether the table Whitelist exists. """

    mycursor, _ = await self.the_database()
    await mycursor.execute("SHOW TABLE STATUS LIKE 'Whitelist'")
    exists = await mycursor.fetchone()
    await mycursor.close()
    if exists:
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

    mycursor, _ = await self.the_database()
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

"""
CREATE TABLE `cards` (
  `card_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `front_value` varchar(300) NOT NULL,
  `back_value` varchar(300) NOT NULL,
  `timestamp` bigint(20) NOT NULL,
  PRIMARY KEY (`card_id`)
) ENGINE=InnoDB AUTO_INCREMENT=16488 DEFAULT CHARSET=utf8mb4
"""

def setup(client) -> None:
  """ Cog's setup function. """

  client.add_cog(FlashCard(client))
