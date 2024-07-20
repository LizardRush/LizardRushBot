@client.tree.command(name="give_coins")
@app_commands.describe(user="The person to give them to", amount="Coins amount")
async def give_coins(interaction: discord.Interaction, user: discord.user, amount: int)
    if message.author.guild_permissions.administrator:
        amount = int(message.content.split()[2])
        data = get_stats(user)
        data["Coins"] += amount
        post_file_to_github("LizardRushBot", f"stats/{user.id}_stats.json", json.dumps(data, indent=4))
        await interaction.response.send_message(f"Gave {amount} coins to {user.name}", emphemral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", emphemral=True)
