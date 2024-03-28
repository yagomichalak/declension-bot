import discord
from discord.ext import commands
from discord import Option, slash_command, SlashCommandGroup, ApplicationContext

import os
import aiohttp
import json

from googletrans import Translator
from others import utils

IS_LOCAL = utils.is_local()
TEST_GUILDS = [os.getenv("TEST_GUILD_ID")] if IS_LOCAL else None


class Tools(commands.Cog):
    """ A command for tool commands. """

    def __init__(self, client) -> None:
        """ Class initializing method. """

        self.client = client
        self.session = aiohttp.ClientSession(loop=client.loop)

    _synonym = SlashCommandGroup('synonym', 'Finds synonyms for a given word in a given language.', guild_ids=TEST_GUILDS)
    _antonym = SlashCommandGroup('antonym', 'Finds antonyms for a given word in a given language.', guild_ids=TEST_GUILDS)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Tells when the cog is ready to use. """

        print('Tools cog is online!')

    @slash_command(name="translate", guild_ids=TEST_GUILDS)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _translate(self, interaction: ApplicationContext,
        language: Option(str, name="to_language", description="The language to translate the message to..", required=True),
        message: Option(str, name="message", description="The message to translate.", required=True),
        source_language: Option(str, name="from_language", description="The source language to translate the message from.", required=False)
    ) -> None:
        """ Translates a message into another language. """

        await interaction.defer(ephemeral=True)
        current_time = await utils.get_time_now()

        trans = Translator(service_urls=['translate.googleapis.com'])
        try:
            if source_language:
                translation = trans.translate(f'{message}', dest=f'{language}')
            else:
                translation = trans.translate(f'{message}', src=source_language, dest=f'{language}')
        except ValueError:
            return await interaction.respond("**Invalid parameter for 'language'!**", ephemeral=True)

        embed = discord.Embed(title="__Translator__",
            description=f"**Translated from `{translation.src}` to `{translation.dest}`**\n\n{translation.text}",
            color=interaction.author.color, timestamp=current_time)
        embed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar)
        await interaction.respond(embed=embed, ephemeral=True)

    @_synonym.command(name="french")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def _synonym_french(self, interaction, search: Option(str, name="search", description="The word you are looking for.", required=True)) -> None:
        """ Searches synonyms of a French word. """

        await interaction.defer(ephemeral=True)
        member = interaction.author
        current_time = await utils.get_time_now()

        url = f"https://dicolink.p.rapidapi.com/mot/{search.strip().replace(' ', '%20')}/synonymes"
        querystring = {"limite": "10"}

        headers = {
            'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
            'x-rapidapi-host': "dicolink.p.rapidapi.com"
        }

        async with self.session.get(url=url, headers=headers, params=querystring) as response:
            if response.status != 200:
                return await interaction.respond(f"**Nothing found, {member.mention}!**", ephemeral=True)

            data = json.loads(await response.read())

            # Makes the embed's header
            embed = discord.Embed(
                title="__French Synonyms__",
                description=f"Showing results for: {search}",
                color=member.color,
                timestamp=current_time
            )

            words = ', '.join(list(map(lambda w: f"**{w['mot']}**", data)))

            # Adds a field for each example
            embed.add_field(name="__Words__", value=words, inline=False)

            # Sets the author of the search
            embed.set_author(name=member, icon_url=member.display_avatar)
            await interaction.respond(embed=embed, ephemeral=True)

    @_antonym.command(name="french")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def _antonym_french(self, interaction, search: Option(str, name="search", description="The word you are looking for.", required=True)) -> None:
        """ Searches antonyms of a French word. """

        await interaction.defer(ephemeral=True)
        member = interaction.author
        current_time = await utils.get_time_now()

        url = f"https://dicolink.p.rapidapi.com/mot/{search.strip().replace(' ', '%20')}/antonymes"
        querystring = {"limite": "10"}

        headers = {
            'x-rapidapi-key': os.getenv('RAPID_API_TOKEN'),
            'x-rapidapi-host': "dicolink.p.rapidapi.com"
        }

        async with self.session.get(url=url, headers=headers, params=querystring) as response:
            if response.status != 200:
                return await interaction.respond(f"**Nothing found, {member.mention}!**", ephemeral=True)

            data = json.loads(await response.read())

            # Makes the embed's header
            embed = discord.Embed(
                title="__French Antonyms__",
                description=f"Showing results for: {search}",
                color=member.color,
                timestamp=current_time
            )

            words = ', '.join(list(map(lambda w: f"**{w['mot']}**", data)))

            # Adds a field for each example
            embed.add_field(name="__Words__", value=words, inline=False)

            # Sets the author of the search
            embed.set_author(name=member, icon_url=member.display_avatar)
            await interaction.respond(embed=embed, ephemeral=True)


    @slash_command(name="get_subscriptions", guild_ids=TEST_GUILDS)
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _get_subscriptions(self, interaction: ApplicationContext) -> None:
        """ Gets the bot's subscriptions. """
        
        await interaction.defer(ephemeral=True)
        subscriptions = await self.client.fetch_entitlements()
            
        await interaction.respond(content=subscriptions, ephemeral=True)

    @slash_command(name="get_skus", guild_ids=TEST_GUILDS)
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _get_skus(self, interaction: ApplicationContext) -> None:
        """ Gets the bot's subscriptions. """
        
        await interaction.defer(ephemeral=True)      
        skus = await self.client.fetch_skus()        
        await interaction.respond(content=skus, ephemeral=True)

    @slash_command(name="has_sub", guild_ids=TEST_GUILDS)
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _has_sub(self, interaction: ApplicationContext) -> None:
        """ Creates a test sku. """
        
        await interaction.defer(ephemeral=True)
        subscriptions = await self.client.fetch_entitlements()
        has_subscription = discord.utils.get(subscriptions, user_id=interaction.author.id)
        
        await interaction.respond(content=f"Do you have it? {has_subscription}", ephemeral=True)


def setup(client) -> None:
    """ Cog's setup function. """

    client.add_cog(Tools(client))
