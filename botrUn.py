import discord
from discord.ext import commands
import subprocess
import asyncio
import os

TOKEN = "YOUR_DISCORD_TOKEN"
PREFIX = "cfx!"
bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

export_counter = 0


async def run_ffmpeg(input_file, output_file, ffmpeg_args):
    cmd = ["ffmpeg", "-y", "-i", input_file] + ffmpeg_args + [output_file]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode()


@bot.event
async def on_ready():
    print(f"✅ CoraFX Bot Online as {bot.user}")


# ✅ Help command
@bot.command(name="helpme")
async def helpme(ctx):
    msg = (
        "**CoraFX Help**\n"
        "`cfx!huesat <hue> <saturation>` (-180 to 180 / -100 to 100)\n"
        "`cfx!pinch <amount> <radius>` (-1 to 1 / 0 to 1)\n"
        "`cfx!swirl <degrees>` (-360 to 360)\n"
        "`cfx!negate`\n"
        "`cfx!audiomixer <gain>` (1 to 10)\n"
        "`cfx!concat` (attach 2 videos)\n"
        "`cfx!ffargs <args>` (custom FFmpeg args)\n"
    )
    await ctx.send(msg)


# ✅ Hue/Saturation
@bot.command(name="huesat")
async def huesat(ctx, hue: float, saturation: float):
    global export_counter
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach a video.")
        return
    attachment = ctx.message.attachments[0]
    input_path = f"in_{export_counter}.mp4"
    output_path = f"out_{export_counter}.mp4"
    export_counter += 1
    await attachment.save(input_path)

    # Hue: -180 to 180, Saturation: -100 to 100 → FFmpeg expects ratio
    hue_val = hue
    sat_val = saturation / 100  # convert percent to FFmpeg scale
    ffmpeg_args = ["-vf", f"hue=h={hue_val}:s={sat_val}"]

    await ctx.send(f"🎨 Applying Hue={hue_val}, Saturation={sat_val}...")
    _, stderr = await run_ffmpeg(input_path, output_path, ffmpeg_args)

    if os.path.exists(output_path):
        await ctx.send(file=discord.File(output_path))
    else:
        await ctx.send("❌ FFmpeg Error")
        print(stderr)


# ✅ Pinch/Punch effect
@bot.command(name="pinch")
async def pinch(ctx, amount: float, radius: float):
    global export_counter
    if not ctx.message.attachments:
        await ctx.send("❌ Attach a video!")
        return
    attachment = ctx.message.attachments[0]
    input_path = f"in_{export_counter}.mp4"
    output_path = f"out_{export_counter}.mp4"
    export_counter += 1
    await attachment.save(input_path)

    # FFmpeg pinch effect: using v360 plugin with barrel distortion
    ffmpeg_args = ["-vf", f"v360=input=rect:output=rect:d_fov={100+amount*50}:ih_fov={100+amount*50}"]

    await ctx.send(f"🔮 Pinch effect: amount={amount}, radius={radius}")
    _, stderr = await run_ffmpeg(input_path, output_path, ffmpeg_args)

    if os.path.exists(output_path):
        await ctx.send(file=discord.File(output_path))
    else:
        await ctx.send("❌ Error")
        print(stderr)


# ✅ Swirl effect
@bot.command(name="swirl")
async def swirl(ctx, degrees: float):
    global export_counter
    if not ctx.message.attachments:
        await ctx.send("❌ Attach a video!")
        return
    attachment = ctx.message.attachments[0]
    input_path = f"in_{export_counter}.mp4"
    output_path = f"out_{export_counter}.mp4"
    export_counter += 1
    await attachment.save(input_path)

    ffmpeg_args = ["-vf", f"swirl=angle={degrees}"]

    await ctx.send(f"🌀 Applying swirl: {degrees}°")
    _, stderr = await run_ffmpeg(input_path, output_path, ffmpeg_args)

    if os.path.exists(output_path):
        await ctx.send(file=discord.File(output_path))
    else:
        await ctx.send("❌ Error")
        print(stderr)


# ✅ Negate effect
@bot.command(name="negate")
async def negate(ctx):
    global export_counter
    if not ctx.message.attachments:
        await ctx.send("❌ Attach a video!")
        return
    attachment = ctx.message.attachments[0]
    input_path = f"in_{export_counter}.mp4"
    output_path = f"out_{export_counter}.mp4"
    export_counter += 1
    await attachment.save(input_path)

    ffmpeg_args = ["-vf", "lutrgb=r=negval:g=negval:b=negval"]

    await ctx.send("🌑 Applying negate effect...")
    _, stderr = await run_ffmpeg(input_path, output_path, ffmpeg_args)

    if os.path.exists(output_path):
        await ctx.send(file=discord.File(output_path))
    else:
        await ctx.send("❌ Error")
        print(stderr)


# ✅ Audio mixer (volume)
@bot.command(name="audiomixer")
async def audiomixer(ctx, gain: float):
    global export_counter
    if not ctx.message.attachments:
        await ctx.send("❌ Attach an audio file!")
        return
    attachment = ctx.message.attachments[0]
    input_path = f"in_{export_counter}.mp3"
    output_path = f"out_{export_counter}.mp3"
    export_counter += 1
    await attachment.save(input_path)

    ffmpeg_args = ["-af", f"volume={gain}"]

    await ctx.send(f"🎚 Audio gain: {gain}")
    _, stderr = await run_ffmpeg(input_path, output_path, ffmpeg_args)

    if os.path.exists(output_path):
        await ctx.send(file=discord.File(output_path))
    else:
        await ctx.send("❌ Error")
        print(stderr)


# ✅ Concat two videos
@bot.command(name="concat")
async def concat(ctx):
    global export_counter
    if len(ctx.message.attachments) < 2:
        await ctx.send("❌ Attach 2 videos!")
        return

    file1 = f"file1_{export_counter}.mp4"
    file2 = f"file2_{export_counter}.mp4"
    output_path = f"out_{export_counter}.mp4"
    export_counter += 1

    await ctx.message.attachments[0].save(file1)
    await ctx.message.attachments[1].save(file2)

    # Create concat list
    with open("concat_list.txt", "w") as f:
        f.write(f"file '{file1}'\nfile '{file2}'\n")

    ffmpeg_args = ["-f", "concat", "-safe", "0", "-i", "concat_list.txt", "-c", "copy"]

    await ctx.send("📼 Concatenating videos...")
    _, stderr = await run_ffmpeg("", output_path, ffmpeg_args)

    if os.path.exists(output_path):
        await ctx.send(file=discord.File(output_path))
    else:
        await ctx.send("❌ Error")
        print(stderr)


# ✅ Custom FFmpeg arguments
@bot.command(name="ffargs")
async def ffargs(ctx, *, args):
    global export_counter
    if not ctx.message.attachments:
        await ctx.send("❌ Attach a video!")
        return
    attachment = ctx.message.attachments[0]
    input_path = f"in_{export_counter}.mp4"
    output_path = f"out_{export_counter}.mp4"
    export_counter += 1
    await attachment.save(input_path)

    ffmpeg_args = args.split()
    await ctx.send(f"⚙ Running FFmpeg with: {args}")
    _, stderr = await run_ffmpeg(input_path, output_path, ffmpeg_args)

    if os.path.exists(output_path):
        await ctx.send(file=discord.File(output_path))
    else:
        await ctx.send("❌ Error")
        print(stderr)


bot.run(TOKEN)
