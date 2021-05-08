import asyncio
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

        if self.player.data['Banned']:
            return False
        return True

    def allCookies(self):
        cookies = []
        for item in self.config['Database Info']:
            try:
                if self.config['Database Info'][item]['IsDessert']:
                    cookies.append(item)
            except KeyError:
                pass
            except TypeError:
                pass
        return cookies

    def isValidCookie(self, checking):
        correctCookies = self.allCookies()
        lowerCookies = [cookie.lower() for cookie in self.allCookies()]
        if checking in lowerCookies:
            return correctCookies[lowerCookies.index(checking)]
        if checking == 'all':
            return checking
        return False

    def sellCookies(self, cookie, count):
        if count < 0:
            count = 0
        if count > self.player.data[cookie]:
            count = self.player.data[cookie]
        price = self.config['Game']['Desserts'][cookie]['Price']
        sellValue = price*count
        self.player.update_value(cookie, self.player.data[cookie]-count)
        self.player.update_value('Balance', self.player.data['Balance']+sellValue)

        return cookie, count, price, sellValue

    def isValidOven(self, checking):
        correctOvens = list(self.config['Game']['Ovens'].keys())
        lowerOvens = [oven.lower() for oven in self.config['Game']['Ovens']]
        if checking in lowerOvens:
            return correctOvens[lowerOvens.index(checking)]
        return False

    @commands.is_owner()
    @commands.command(name='Update', aliases=[])
    async def OWNER_CMD_update(self, ctx, purge=None):
        embed = discord.Embed(title=f'Updated Player Fields! {"**PURGED**" if purge else ""}', color=discord.Color.green())
        embed.add_field(name='Added Field(s)', value=f'{", ".join(self.player.added_fields) if self.player.added_fields else "No Fields Added"}', inline=False)
        embed.add_field(name='Removed Field(s)', value=f'{", ".join(self.player.removed_fields) if self.player.removed_fields else "No Fields Removed"}', inline=False)
        embed.set_footer(text=f'Player fields: {len(self.player.data.keys())}')
        await ctx.send(embed=embed)

        if purge.lower() == 'purge':
            self.player.purgeAll()

    @commands.is_owner()
    @commands.command(name='Fields', aliases=[])
    async def OWNER_CMD_fields(self, ctx):
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
            embed.add_field(name="Burned Cookies", value=f"{sum(cooked.values())}x {self.config['Game']['Desserts']['BurnedCookies']['Icon']}")
            embed.set_footer(text='Tired of burning cookies? Upgrade to a better oven!')
            await ctx.send(embed=embed)

            self.player.update_value('BurnedCookies', self.player.data['BurnedCookies'] + sum(cooked.values()))
        else:
            cookedMessage = []
            for cookie in cooked:
                cookedMessage.append(f"{self.config['Game']['Desserts'][cookie]['Icon']} {cooked[cookie]:,}")
                self.player.update_value(cookie, self.player.data[cookie] + cooked[cookie])
            embed = discord.Embed(title='Yum!', color=discord.Color.green())
            embed.add_field(name="You baked some cookies!", value="\n".join(cookedMessage))
            embed.set_footer(text='Want a better yield? Upgrade to a better oven!')
            await ctx.send(embed=embed)

    @commands.command(name='Profile', aliases=['me', 'user', 'p', 'bal'], help='View you profile or another users profile', usage='Profile [user]')
    async def CMD_profile(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        viewing = utils.player.Player(bot=self.bot, ctx=ctx, user=user)

        embed = discord.Embed(title=user if not viewing.data['Banned'] else f"{user} **BANNED**", color=discord.Color.green() if not viewing.data['Banned'] else discord.Color.red())
        embed.add_field(name="Level", value=f"{viewing.data['Level']} ({viewing.data['XP']}/0)", inline=True)
        embed.add_field(name="Balance", value=f"${viewing.data['Balance']:,}", inline=True)
        embed.add_field(name="Cookies", value="\n".join([f"{self.config['Game']['Desserts'][cookie]['Icon']} {viewing.data[cookie]:,}" for cookie in self.allCookies()]), inline=False)
        embed.add_field(name="Oven", value=viewing.data['Oven'], inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='Sell', aliases=['s'], help='Sell some cookies', usage='Sell <count> <cookie>')
    async def CMD_sell(self, ctx, count, cookie=None):
        count = count.lower()

        try:
            count = int(count)
        except ValueError:
            if count == 'all':
                count = float('inf')

        if cookie is None:
            embed = discord.Embed(color=discord.Color.orange())
            embed.add_field(name=f'Do you want to sell {count:,} of **ALL** cookies?' if count != float('inf') else f'Do you want to sell **ALL** cookies?', value='This can not be undone! (Y/N)')
            embed.set_footer(text="To sell a single cookie do 'sell <count> [type]'")
            confirm_msg = await ctx.send(embed=embed)
            try:
                confirm = await self.bot.wait_for('message', check=lambda msg: msg.author.id == ctx.author.id, timeout=60.0)
                if confirm.content.lower() in ['y', 'ye', 'yes']:
                    cookie = 'all'
                    await confirm_msg.delete()
                else:
                    embed = discord.Embed(color=discord.Color.red())
                    embed.add_field(name='Okay!', value='Your cookies have not been sold')
                    embed.set_footer(text="To sell a single cookie do 'sell <count> [type]'")
                    await confirm_msg.update(embed=embed)
            except asyncio.TimeoutError:
                embed = discord.Embed(color=discord.Color.red())
                embed.add_field(name='Took too long!', value='Your cookies have not been sold')
                embed.set_footer(text="To sell a single cookie do 'sell <count> [type]'")
                await confirm_msg.edit(embed=embed)

        cookie = self.isValidCookie(cookie.lower())

        soldCookies = []
        beforeSell = self.player.data['Balance']

        if cookie:
            if cookie == 'all':
                for cookie in self.allCookies():
                    soldCookies.append(self.sellCookies(cookie, count))
            else:
                soldCookies.append(self.sellCookies(cookie, count))
        else:
            return await ctx.send('Not valid cookie')

        totalEarned = self.player.data['Balance'] - beforeSell

        embed = discord.Embed(color=discord.Color.green())
        embed.add_field(name='Sold!', value="\n".join([f"{self.config['Game']['Desserts'][cookie]['Icon']} {cookie} - {count:,} *(${sellValue:,})*" for cookie, count, price, sellValue in soldCookies]))
        embed.set_footer(text=f'Total cash earned: ${totalEarned:,}')

        await ctx.send(embed=embed)

    @commands.command(name='Shop', aliases=[], help='See all items you can buy', usage='Shop')
    async def CMD_shop(self, ctx):
        ovens = []
        for oven in self.config['Game']['Ovens']:
            if oven == self.player.data['Oven']:
                ovens.append(f'- 🟦 **{oven}**')
            elif oven in self.player.data['OwnedOvens'].split(','):
                ovens.append(f'- 🟩 {oven}')
            else:
                ovens.append(f'- 🟥 {oven} **${self.config["Game"]["Ovens"][oven]["Price"]:,}**')

        embed = discord.Embed(color=discord.Color.teal())
        embed.add_field(name='Ovens', value="\n".join(ovens))
        embed.set_footer(text=f'Current Balance: ${self.player.data["Balance"]:,}')
        await ctx.send(embed=embed)

    @commands.command(name='Buy', aliases=[], help='Buy an item from the shop', usage='Buy <category> <item>')
    async def CMD_buy(self, ctx, category, *, item):
        category = category.lower()
        item = item.lower().replace(" ", "")
        if category in ['ovens', 'oven', 'o']:
            item = self.isValidOven(item)
            if item in self.config['Game']['Ovens'].keys():
                if self.player.data['Balance'] >= self.config['Game']['Ovens'][item]['Price']:
                    self.player.update_value('Balance', self.player.data['Balance'] - self.config['Game']['Ovens'][item]['Price'])
                    self.player.update_value('OwnedOvens', f'{self.player.data["OwnedOvens"]},{item}')
                    embed = discord.Embed(color=discord.Color.green())
                    embed.add_field(name="You have bought a new oven!", value="To switch ovens use the `oven` command")
                else:
                    embed = discord.Embed(color=discord.Color.orange())
                    embed.add_field(name="You don't have enough money to buy this oven!", value="To get more money sell come cookies!")
                    embed.set_footer(text=f"You need another ${self.config['Game']['Ovens'][item]['Price'] - self.player.data['Balance']:,} to buy this oven")
            else:
                embed = discord.Embed(color=discord.Color.red())
                embed.add_field(name="Sorry, I don't have that oven in stock!", value="How about you take another look around the shop")
        else:
            embed = discord.Embed(color=discord.Color.red())
            embed.add_field(name=f"Sorry we don't sell `{item}'s` here!", value="We only sell Ovens currently")
        await ctx.send(embed=embed)

    @commands.command(name="Ovens", aliases=['Oven'], help="Change your current oven", usage='Oven [oven]')
    async def CMD_oven(self, ctx, *, oven=None):
        oven = self.isValidOven(oven.lower().replace(" ", "")) if oven else oven
        if oven:
            if oven in self.player.data['OwnedOvens'].split(","):
                embed = discord.Embed(title="Switched Ovens!", color=discord.Color.green())
                embed.add_field(name="Old Oven", value=self.player.data['Oven'])
                self.player.update_value("Oven", oven)
                embed.add_field(name="New Oven", value=self.player.data['Oven'])
            else:
                embed = discord.Embed(color=discord.Color.red())
                embed.add_field(name="Failed to switch", value="You don't own this oven!")
                embed.set_footer(text=f"You can buy this oven in the shop for ${self.config['Game']['Ovens'][oven]['Price']:,}")
        elif oven is None:
            selectedOven = None
            ownedOvens = []
            otherOvens = []
            for oven in self.config['Game']['Ovens']:
                if oven == self.player.data['Oven']:
                    selectedOven = f'- **{oven}**'
                elif oven in self.player.data['OwnedOvens'].split(','):
                    ownedOvens.append(f'- {oven}')
                else:
                    otherOvens.append(f'- {oven}')

            embed = discord.Embed(title="Ovens", color=discord.Color.teal())
            embed.add_field(name="🟦 Selected Oven", value=selectedOven, inline=False)
            embed.add_field(name="🟩 Owned Ovens", value="\n".join(ownedOvens) if ownedOvens else 'None', inline=False)
            embed.add_field(name="🟥 Unowned Ovens", value="\n".join(otherOvens) if otherOvens else 'None', inline=False)
        else:
            embed = discord.Embed(color=discord.Color.red())
            embed.add_field(name="Invalid Oven", value="Hmmm...I cant seem to find that oven. Make sure you are using the right name")
            embed.set_footer(text="View all ovens with the 'oven' command")
        await ctx.send(embed=embed)
        pass


def setup(bot):
    bot.add_cog(General(bot))
