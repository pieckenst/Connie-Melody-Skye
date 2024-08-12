import discord
from discord.ext import commands
from discord import ButtonStyle, SelectOption, Interaction
from discord.ui import Button, Select, View
import contextlib

class Dropdown(discord.ui.Select):
    """
    A dropdown menu that allows the user to select a category from a list of available categories. When a category is selected, the `get_help` function is called with the selected category to display the help information for that category.
    
    The `Dropdown` class inherits from `discord.ui.Select` and is used as part of the `DropdownView` class to create the dropdown menu. The `callback` method is called when the user selects an option from the dropdown menu, and it handles the logic for displaying the help information for the selected category.
    
    If the user selects the "Close" option, the help embed is updated to display a message indicating that the help menu has been closed.
    """
    def __init__(self, options, ctx):
        self.bot = ctx.bot
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        label = self.values[0]
        for cog in self.bot.cogs:
            if label == cog:
                await get_help(self, interaction, CogToPassAlong=cog)
                return
        if label == "Close":
            embede = discord.Embed(title=f"{self.bot.user.name} Help", description="", color=discord.Color.blurple())
            embede.set_footer(
                text="Use help [command] or help [category] for more information | <> is required | [] is optional"
            )
            await interaction.response.edit_message(embed=embede, view=None)

class DropdownView(discord.ui.View):
    def __init__(self, options, ctx):
        super().__init__()
        self.bot = ctx
        self.add_item(Dropdown(options, self.bot))

class Help(commands.Cog):
    "The Help Menu Cog"
    def __init__(self, bot):
        self.bot = bot
        self.bot.help_command = MyHelp()

class HelpEmbed(discord.Embed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = discord.utils.utcnow()
        text = "Use help [command] or help [category] for more information | <> is required | [] is optional"
        self.set_footer(text=text)
        self.color = discord.Color.blurple()

class MyHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={"help": "The help command for the bot"}
        )

    async def send(self, **kwargs):
        await self.get_destination().send(**kwargs)

    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = HelpEmbed(title=f"{ctx.me.display_name} Help")
        usable = 0
        myoptions = []
        view = DropdownView(myoptions, ctx)

        for cog, commands in mapping.items():
            if filtered_commands := await self.filter_commands(commands):
                amount_commands = len(filtered_commands)
                usable += amount_commands
                if cog:
                    name = cog.qualified_name
                    description = cog.description or "No description"
                else:
                    name = "No Category"
                    description = "Commands with no category"
                myoptions.append(SelectOption(label=name, value=name))

        myoptions.append(SelectOption(label="Close", value="Close"))
        await self.send(embed=embed, view=view)

    async def send_command_help(self, command):
        signature = self.get_command_signature(command)
        embed = HelpEmbed(title=signature, description=command.brief or "No help found...")

        if cog := command.cog:
            embed.add_field(name="Category", value=cog.qualified_name)

        can_run = "No"
        with contextlib.suppress(commands.CommandError):
            if await command.can_run(self.context):
                can_run = "Yes"

        embed.add_field(name="Usable", value=can_run)

        if command._buckets and (cooldown := command._buckets._cooldown):
            embed.add_field(
                name="Cooldown",
                value=f"{cooldown.rate} per {cooldown.per:.0f} seconds",
            )

        await self.send(embed=embed)

    async def send_help_embed(self, title, description, commands):
        embed = HelpEmbed(title=title, description=description or "No help found...")

        if filtered_commands := await self.filter_commands(commands):
            for command in filtered_commands:
                embed.add_field(name=self.get_command_signature(command), value=command.brief or "No help found...")

        await self.send(embed=embed)

    async def send_group_help(self, group):
        title = self.get_command_signature(group)
        await self.send_help_embed(title, group.help, group.commands)

    async def send_cog_help(self, cog):
        title = cog.qualified_name or "No"
        await self.send_help_embed(f"{title} Category", cog.description, cog.get_commands())

async def get_help(self, interaction, CogToPassAlong):
    """
        Generates a help embed for a specific cog in the Discord bot.
    
        Parameters:
        - `interaction`: The Discord interaction object.
        - `CogToPassAlong`: The name of the cog to generate help for.
    
        The function retrieves the commands for the specified cog, creates a Discord embed with the cog's name and description, and then adds fields for each command in the cog (excluding hidden commands). The embed is then sent as the response to the interaction.
            for _ in self.bot.get_cog(CogToPassAlong).get_commands():
            pass
    """
    emb = discord.Embed(
        title=f"{CogToPassAlong} - Commands",
        description=self.bot.cogs[CogToPassAlong].__doc__,
        color=discord.Color.blurple(),
    )
    emb.set_author(name="Help System")
    for command in self.bot.get_cog(CogToPassAlong).get_commands():
        if not command.hidden:
            emb.add_field(name=f"`{command.name}`", value=command.help, inline=True)
    await interaction.response.edit_message(embed=emb)

async def setup(bot):
    await bot.add_cog(Help(bot))
