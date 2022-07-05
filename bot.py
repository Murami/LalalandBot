import interactions

bot = interactions.Client(token="OTkzODE1NTgwODgyNzYzODI2.GujqRY.XkxR433v0pObmHHr7ii9KwZgFO2Wtydi-sTcqY")

@bot.command(
    name="hello",
    description="hello"
)
async def hello_command(ctx: interactions.CommandContext):
    await ctx.send("Hello There !")
    
bot.start()