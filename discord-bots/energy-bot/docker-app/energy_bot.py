import discord
import subprocess
import os

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

GUILD_ID = os.getenv("GUILD_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=GUILD_ID))

@tree.command(name="getusage", description="Fetches power usage from your server", guild=discord.Object(id=GUILD_ID))
async def getusage(interaction: discord.Interaction):
    await interaction.response.defer()  # Acknowledge the command

    try:
        result = subprocess.check_output(
            ['curl', '-ks', 'http://kasa-flask-server-exporter.kasa-flask-server:9101/metrics'],
            text=True
        )
        usage_lines = []
        for line in result.splitlines():
            if line.startswith("kasapower_watts"):
                parts = line.split('"')
                if len(parts) > 1:
                    device = parts[1]
                    value = line.split()[-1]
                    usage_lines.append(f"**{device}**: {value} W")

        message = "\n".join(usage_lines) or "No usage data found."
        await interaction.followup.send(f"🔌 Power Usage:\n{message}")

    except Exception as e:
        await interaction.followup.send(f"Error fetching usage: {str(e)}")

client.run(BOT_TOKEN)
