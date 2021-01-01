import discord
import config

client = discord.Client()

@client.event
async def on_ready():
    print('Bot successfully logged in as: {0.user}'.format(client))


@client.event
async def on_message(message):
    print(message)
    if message.author == client.user:
        return
    
    if message.content.startswith('$hello'):
        await message.channel.send('Hello {message.author.name}!'.format(message=message))

client.run(config.bot_token)