import json
import os
import random

import discord
from discord.ext import commands

import utils.player


class General(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.player = None
        self.bot = bot

    def cog_check(self, ctx):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.player = utils.player.Player(bot=self.bot, ctx=ctx, user=ctx.author)
        return True  # return False to prevent command usage

    @commands.is_owner()
    @commands.command(name='Update', aliases=[])
    async def CMD_update(self, ctx):
        embed = discord.Embed(title='Updated Player Fields!', color=discord.Color.green())
        embed.add_field(name='Added Field(s)', value=f'{", ".join(self.player.added_fields) if self.player.added_fields else "No Fields Added"}', inline=False)
        embed.add_field(name='Removed Field(s)', value=f'{", ".join(self.player.removed_fields) if self.player.removed_fields else "No Fields Removed"}', inline=False)
        embed.set_footer(text=f'Player fields: {len(self.player.data.keys())}')
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name='Fields', aliases=[])
    async def CMD_fields(self, ctx):
        await ctx.send(self.player.data)

    @commands.command(name='Cook', aliases=[], help=f'Bake some cookies :)', usage=f'Cook')
    async def CMD_cook(self, ctx):
        cooked = {}
        burnChance = random.randint(1, 100)
        for cookie in self.config['Game']['Ovens'][self.player.data['Oven']]['Can Cook'].keys():
            cookChance = random.randint(1, 100)
            if cookChance <= self.config['Game']['Ovens'][self.player.data['Oven']]['Can Cook'][cookie]['Rate']:
                cooked[cookie] = random.randint(self.config['Game']['Ovens'][self.player.data['Oven']]['Can Cook'][cookie]['Min'], self.config['Game']['Ovens'][self.player.data['Oven']]['Can Cook'][cookie]['Max'])
        if burnChance <= self.config['Game']['Ovens'][self.player.data['Oven']]['Burn Rate']:
            embed = discord.Embed(title='Oh no! You burned your cookies!', color=discord.Color.red())
            embed.add_field(name="Burned Cookies", value=f"{sum(cooked.values())}x {self.config['Game']['Desserts']['BurnedIcon']}")
            embed.set_footer(text='Tired of burning cookies? Upgrade to a better oven!')
            await ctx.send(embed=embed)

            self.player.update_value('BurnedCookies', self.player.data['BurnedCookies'] + sum(cooked.values()))
        else:
            cookedMessage = []
            for cookie in cooked:
                cookedMessage.append(f"{self.config['Game']['Desserts'][cookie]['Icon']}x {cooked[cookie]}")
                self.player.update_value(cookie, self.player.data[cookie] + cooked[cookie])
            embed = discord.Embed(title='Yum!', color=discord.Color.green())
            embed.add_field(name="You baked some cookies!", value="\n".join(cookedMessage))
            embed.set_footer(text='Want a better yield? Upgrade to a better oven!')
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
