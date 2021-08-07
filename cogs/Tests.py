import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_option, create_choice, create_permission, create_multi_ids_permission


TEST_GUILDS = [777886754761605140]


class Tests(commands.Cog):
  """ A category for conjugation commands. """

  def __init__(self, client) -> None:
    """ Init method of the conjugation class. """
    self.client = client


  @commands.Cog.listener()
  async def on_ready(self):
    print('Tests cog is online!')

#   @cog_ext.cog_slash(name="dnk", description="Tells you something about DNK.", guild_ids=TEST_GUILDS)
#   async def _dnk(self, ctx: SlashContext):
#     await ctx.send(f"**DNK est toujours là pour les vrais !**")


def setup(client) -> None:
    client.add_cog(Tests(client))