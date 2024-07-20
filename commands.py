@client.tree.command(name="give_coins")
@app_commands.describe(user="The person to give them to", amount="Coins amount")
async def give_coins(interaction: discord.Interaction, user: discord.user, amount: int):
    if interaction.user.guild_permissions.administrator:
        amount = int(message.content.split()[2])
        data = get_stats(user)
        data["Coins"] += amount
        post_file_to_github("LizardRushBot", f"stats/{user.id}_stats.json", json.dumps(data, indent=4))
        await interaction.response.send_message(f"Gave {amount} coins to {user.name}", emphemral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", emphemral=True)

@client.tree.command(name="warn")
@app_commands.describe(user="The person to warn")
async def warn(interaction: discord.Interaction, user: discord.user):
    data = get_stats(user)
    if interaction.user.guild_permissions.administrator and not user.guild_permissions.administator:
        if data['Warnings'] == 3:
            await message.reply(f'{i.name} has been banned for 3 warnings.')
            await i.ban(reason='3 warnings')
        else:
            data['Warnings'] += 1
            f.seek(0)
            json.dump(data, f, indent=4)
            await interaction.response.send_message(f"Warned {user.display_name}", empheral=True)
    else:
        await interaction.response.send_message("You cannot warn that user", empheral=True)

@client.tree.command(name="invite")
async def invite(interaction: discord.Interaction):
    await interaction.response.send_message("This bot's invite link is [https://discord.gg/LizardBot](https://discord.com/oauth2/authorize?client_id=1197661699826798622&permissions=8&integration_type=0&scope=bot", empheral=True)

@client.tree.command(name="trap")
@app_commands.describe(user="The person to trap")
async def trap(interaction: discord.Interaction, user: discord.user):
    if interaction.user.guild_permissions.manage_roles:
        # Check if the mentioned user has administrative permissions
        if user.guild_permissions.administrator:
            await interaction.response.send_message("You cannot trap a user with administrative permissions.", empheral=True)
        else:
            trapped_role = discord.utils.get(interaction.guild.roles, name="Trapped")
            if not trapped_role:
                trapped_role = await message.guild.create_role(name="Trapped", permissions=discord.Permissions.none())
            await user.add_roles(trapped_role)
        await interaction.response.send_message(f"{user.mention} has been trapped and cannot send messages.")
    else:
        await interaction.response.send_message("You don't have the Manage Roles permission to use this command.", empheral=True)

@client.tree.command(name="crucifix")
@app_commands.describe(user="The person to crucify")
async def crucifix(interaction: discord.Interaction):
    if interaction.user.guild_permissions.ban_members:
        # Check if the mentioned user has administrative permissions
        if user.guild_permissions.administrator:
            await interaction.response.send_message("You cannot crucify a user with administrative permissions.", empheral=True)
        else:
            trapped_role = discord.utils.get(interaction.guild.roles, name="Trapped")
            if not trapped_role:
                trapped_role = await interaction.guild.create_role(name="Trapped", permissions=discord.Permissions.none())
            await user.add_roles(trapped_role)
        await interaction.response.send_message(f"{user.mention} has been trapped and cannot send messages.", empheral=False)
    else:
        await interaction.response.send_message("You don't have the Ban Users permission to use this command.", empheral=True)

@client.tree.command(name="crucifix_trapped")
async def crucifix_trap(interaction: discord.Interaction):
    if interaction.user:
        trapped_role = discord.utils.get(message.guild.roles, name="Trapped")
        if trapped_role:
            trapped_members = [member for member in message.guild.members if trapped_role in member.roles]
            for member in trapped_members:
                try:
                    await interaction.guild.ban(member)
                    await interaction.response.send_message(f"{member.mention} has been banned.")
                except discord.Forbidden:
                    await interaction.response.send_message("I don't have the necessary permissions to ban members.")
        else:
            await interaction.response.send_message("No one is trapped.", empheral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", empheral=True)

@client.tree.command(name="grant_admin")
@app_commands.describe(user="The person to grant admin perms to")
async def grant_admin(interaction: discord.Interaction, user: discord.user):
    if interaction.user.guild_permissions.administrator:
        admin_role = discord.utils.get(interaction.guild.roles, name="Admin")
        if not admin_role:
            admin_role = await interaction.guild.create_role(name="Admin", permissions=discord.Permissions(administrator=True))
        await user.add_roles(admin_role)
        interaction.response.send_message(f"{user.mention} has been granted admin permissions.")
    else:
        await interaction.response.send_message("You don't have permission to use this command.", empheral=True)

@client.tree.command(name="send_rules")
async def send_rules(interaction:discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        channel = discord.utils.get(interaction.guild.channels, "rulebook")
        embed = create_embed(color=0x0D98BA, description=requests.get(f"{handle}rules.txt").text.replace("\n", "\n\n"), title="Da Rules")
