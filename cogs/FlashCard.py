import discord
from discord.ext import commands
import aiomysql
import os
from typing import Any, List, Dict, Union, Callable
import asyncio
from functools import reduce
from datetime import datetime
from others.customerrors import NotInWhitelist

class NotInWhitelist(CheckFailure): pass

class FlashCard(commands.Cog, command_attrs=dict(hidden=False)):
  """ A category for creating, editing, deleting and showing 'FlashCard'."""

  def __init__(self, client) -> None:
    """Class initializing method."""

    self.client = client
    self.loop = asyncio.get_event_loop()
    self.server_id = int(os.getenv('SERVER_ID'))
    self.whitelist: List[int] = []

  
  @commands.Cog.listener()
  async def on_ready(self) -> None:
    """ Tells when the cog is ready to use. """

    if await self.table_exists_whitelist():
      self.whitelist = await self.get_whitelist()
      
    print('FlashCard cog is online')

  # Discord commands

  def check_whitelist():
    async def real_check(ctx):
      if ctx.guild.id in ctx.command.cog.whitelist:
          return True
      raise NotInWhitelist()
    return commands.check(real_check)


  @commands.command(aliases=['addc', 'ac'])
  @commands.cooldown(1, 120, commands.BucketType.user)
  @check_whitelist()
  async def add_card(self, ctx) -> None:
    """ Adds a card into the database. """

    if not ctx.guild or ctx.guild.id not in self.whitelist:
      return await ctx.send("**This server is not whitelisted!**")

    member = ctx.author
    # Makes initial embed
    embed = discord.Embed(
      color=member.color,
      timestamp=ctx.message.created_at
    )
    embed.set_footer(text="60 seconds to answer...")

    # Gets the value for the front side of the card
    embed.title ="Type a value for the **`front`** part of your card."
    bot_msg = await ctx.send(embed=embed)
    front = await self.get_message(member, bot_msg, ctx.channel, embed)
    if front is None:
      self.client.get_command('add_card').reset_cooldown(ctx)
      return

    # Gets the value for the back side of the card
    embed.title = "Type a value for the **`back`** part of your card"
    bot_msg = await ctx.send(embed=embed)
    back = await self.get_message(member, bot_msg, ctx.channel, embed)
    if back is None:
      self.client.get_command('add_card').reset_cooldown(ctx)
      return

    # Adds a field for the front and back side of the card
    embed.add_field(name="__Front__", value=f"```{front}```", inline=False)
    embed.add_field(name="__Back__", value=f"```{back}```", inline=False)

    # Asks user for confirmation of informed values
    embed.title = "Do you want to confirm the values below?"
    bot_msg = await ctx.send(embed=embed)
    reaction = await self.get_reaction(member, bot_msg, embed)
    if reaction == '✅':
      self.client.get_command('add_card').reset_cooldown(ctx)
      epoch = datetime.utcfromtimestamp(0)
      the_time = (datetime.utcnow() - epoch).total_seconds()
      inserted = await self._insert_card(ctx.guild.id, member.id, front, back, the_time)
      if inserted:
        await ctx.send("**Values confirmed! Added them into the DB...**")
      else:
        await ctx.send("**Values confirmed! But this server is not whitelisted...**")
    elif reaction == '❌':
      return await ctx.send("**Values not confirmed! Not adding them into the DB...**")
	
  @commands.command(aliases=['delc', 'dc', 'del_card'])
  @commands.cooldown(1, 5, commands.BucketType.user)
  @check_whitelist()
  async def delete_card(self, ctx, card_id: int = None) -> None:
    """ Deletes a card from the user's deck. 
    :param card_id: The ID of the card that is gonna be deleted. """

    if not ctx.guild or ctx.guild.id not in self.whitelist:
      return await ctx.send("**This server is not whitelisted!**")

    member = ctx.author
    if not card_id:
      self.client.get_command().reset_cooldown()
      return await ctx.send(f"**You need to inform a card ID, {member.mention}!**")

    if not await self.card_exists(member.id, card_id):
      return await ctx.send(f"**You don't have a card with that ID, {member.mention}!**")

    await self._delete_card(member.id, card_id)
    await ctx.send(f"**Card with ID `{card_id}` was successfully deleted from your deck, {member.mention}!**")

  @commands.command(aliases=['cds'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  @check_whitelist()
  async def cards(self, ctx):
    """ Shows all cards of a particular user. """

    if not ctx.guild or ctx.guild.id not in self.whitelist:
      return await ctx.send("**This server is not whitelisted!**")

    member = ctx.author
    cards = await self.get_user_cards(member.id)
    msg = await ctx.send(embed=discord.Embed(title="**Opening deck...**"))
    return await self.pagination_looping(ctx, member, msg, cards)

  @commands.command(aliases=['sc', 'scs', 'search_card', 'search'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  @check_whitelist()
  async def search_cards(self, ctx, *, values: str = None) -> None:
    """ Searches for cards in the user's deck with the given search values. 
    :param values: What is gonna be searched in the DB.
    """
    if not ctx.guild or ctx.guild.id not in self.whitelist:
      return await ctx.send("**This server is not whitelisted!**")

    member = ctx.author

    if not values:
      self.client.get_command('search_cards').reset_cooldown(ctx)
      return await ctx.send(f"**Please, inform something to search for, {member.mention}!**")

    if len(values) > 300:
      return await ctx.send(f"Your search values have to be within 300 characters maximum, {member.mention}!**")

    if values := await self.fetch_values(member.id, values):
      msg = await ctx.send("**This is what I found...**")
      return await self.pagination_looping(ctx, member, msg, values)
    else:
      await ctx.send(f"**Nothing found with the given values, {member.mention}!**")      


  async def pagination_looping(self, ctx: commands.Context, member: discord.Member, msg: discord.Message, the_list: List[List[Any]]) -> None:
    """ Makes an infinite loop for paginating embedded messages. """

    embed = discord.Embed(
      description=f"**Total of cards:** {len(the_list)}",
      color=member.color,
      timestamp=ctx.message.created_at
    )

    index = 0
    
    await asyncio.sleep(0.5)
    await msg.add_reaction('⬅️')
    await msg.add_reaction('➡️')
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

      await msg.edit(embed=embed)

      try:
        r, _ = await self.client.wait_for('reaction_add', timeout=60, 
        check=lambda r, u: u.id == member.id and r.message.id == msg.id and r.message.guild and \
        str(r.emoji) in ['⬅️', '➡️']
        )
				
      except asyncio.TimeoutError:
        await msg.remove_reaction('⬅️', self.client.user)
        await msg.remove_reaction('➡️', self.client.user)
        break

      else:
        if str(r.emoji) == "➡️":
          await msg.remove_reaction(r.emoji, member)
          if index < (len(the_list) - 2):
            index += 2
          continue
        elif str(r.emoji) == "⬅️":
          await msg.remove_reaction(r.emoji, member)
          if index > 0:
            index -= 2
          continue



  # Get user response methods

  async def get_message(self, member: discord.Member, msg: discord.Message, channel: discord.TextChannel, embed: discord.Embed) -> Union[str, None]:
    """ Gets user's message response. """

    def check(m: discord.Message) -> bool:
      if m.author == member and m.guild and m.channel.id == channel.id:
        if len(m.content) <= 300:
          return True
        else:
          self.client.loop.create_task(channel.send("**Your answer must be within 300 characters**"))
      else:
        return False

    try:
      message = await self.client.wait_for('message', timeout=60, 
    check=check)
    except asyncio.TimeoutError:
      embed.title = "**Timeout! Try again.**"
      embed.color = discord.Color.red()
      await msg.edit(embed=embed)
      return None
    else:
      content = message.content
      return content

  async def get_reaction(self, member, msg: discord.Message, embed: discord.Embed) -> Union[str, None]:
    """ Gets user's reaction response. """

    def check(r: discord.Reaction, u: discord.Member) -> bool:
      return u.id == member.id and r.message.id == msg.id and r.message.guild and str(r.emoji) in ['✅', '❌']

    await msg.add_reaction('✅')
    await msg.add_reaction('❌')
    try:
      reaction, _ = await self.client.wait_for('reaction_add', 
      timeout=60, check=check)
    except asyncio.TimeoutError:
      embed.title = "**Timeout, not adding it!**"
      embed.color = discord.Color.red()
      await msg.remove_reaction('✅', self.client.user)
      await msg.remove_reaction('❌', self.client.user)
      await msg.edit(embed=embed)
      return None
    else:
      return str(reaction.emoji)

  # Database methods

  @commands.command(hidden=True)
  @commands.is_owner()
  async def create_table(self, ctx) -> None:
    """ Creates the Cards table. """

    if await self.table_exists():
      return await ctx.send("**The __Cards__ table already exists!**")

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
    await ctx.send("**Table __Cards__ created!**")

  @commands.command(hidden=True)
  @commands.is_owner()
  async def drop_table(self, ctx) -> None:
    """ Drops the Cards table. """

    if not await self.table_exists():
      return await ctx.send("**The __Cards__ table doesn't exist!**")

    mycursor, db = await self.the_database()
    await mycursor.execute("DROP TABLE Cards")
    await db.commit()
    await mycursor.close()
    await ctx.send("**Table __Cards__ dropped!**")

  @commands.command(hidden=True)
  @commands.is_owner()
  async def reset_table(self, ctx) -> None:
    """ Resets the Cards table. """

    if not await self.table_exists():
      return await ctx.send("**The __Cards__ table doesn't exist yet!**")

    mycursor, db = await self.the_database()
    await mycursor.execute("DELETE FROM Cards")
    await db.commit()
    await mycursor.close()
    await ctx.send("**Table __Cards__ reset!**")

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

  @commands.command(aliases=['whitelist', 'ws', 'insert'], hidden=True)
  @commands.is_owner()
  async def insert_server(self, ctx, server_id: int = None) -> None:

    member = ctx.author
    if not server_id:
      return await ctx.send(f"**Please, inform a server ID, {member.mention}!**")

    try:
      await self._insert_server(server_id)
      await ctx.send(f"**The informed server is now whitelisted, {member.mention}!**")
    except Exception as e:
      print(e)
      await ctx.send(f"**It looks like this server was already whitelisted!**")


  @commands.command(aliases=['remove_server'], hidden=True)
  @commands.is_owner()
  async def delete_server(self, ctx, server_id: int = None) -> None:

    member = ctx.author
    if not server_id:
      return await ctx.send(f"**Please, inform a server ID, {member.mention}!**")

    await self._delete_server(server_id)
    await ctx.send(f"**The informed server was removed from the whitelist, {member.mention}!**")

  @commands.command(hidden=True)
  @commands.is_owner()
  async def create_table_whitelist(self, ctx) -> None:
    """ Creates the Whitelist table. """

    if await self.table_whitelist_exists():
      return await ctx.send("**The __Cards__ table already exists!**")

    mycursor, db = await self.the_database()
    await mycursor.execute("""CREATE TABLE Whitelist (
      server_id BIGINT NOT NULL,
      PRIMARY KEY (server_id)
    ) DEFAULT CHARSET=utf8mb4""")
    await db.commit()
    await mycursor.close()
    await ctx.send("**Table __Cards__ created!**")

  @commands.command(hidden=True)
  @commands.is_owner()
  async def drop_table_whitelist(self, ctx) -> None:
    """ Drops the Whitelist table. """

    if not await self.table_exists_whitelist():
      return await ctx.send("**The __Whitelist__ table doesn't exist!**")

    mycursor, db = await self.the_database()
    await mycursor.execute("DROP TABLE Whitelist")
    await db.commit()
    await mycursor.close()
    await ctx.send("**Table __Whitelist__ dropped!**")

  @commands.command(hidden=True)
  @commands.is_owner()
  async def reset_table_whitelist(self, ctx) -> None:
    """ Resets the Cards table. """

    if not await self.table_exists_whitelist():
      return await ctx.send("**The __Whitelist__ table doesn't exist yet!**")

    mycursor, db = await self.the_database()
    await mycursor.execute("DELETE FROM Whitelist")
    await db.commit()
    await mycursor.close()
    await ctx.send("**Table __Whitelist__ reset!**")

  async def table_exists_whitelist(self) -> bool:
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

  async def get_whitelist(self, ctx) -> List[int]:
    """ Gets all existing servers that are in the whitelist. """

    mycursor, db = await self.the_database()
    await mycursor.execute("SELECT server_id FROM Whitelist")
    whitelist = list(reduce(lambda s: s[0], await mycursor.fetchall()))
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