from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

root = Path('/home/ubuntu/AI-News-Tech-Business')
background = Image.open(root / 'demo_reel_background.png').convert('RGB').resize((1080, 1920))
font_path = root / 'Battambang-Bold.ttf'
font_big = ImageFont.truetype(str(font_path), 58)
font_medium = ImageFont.truetype(str(font_path), 39)
font_small = ImageFont.truetype(str(font_path), 30)

overlay = Image.new('RGBA', background.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

def rounded_box(xy, fill, radius=24):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

# Top brand strip.
rounded_box((55, 65, 510, 145), (8, 21, 54, 225), 22)
draw.text((83, 82), 'AI NEWS • TECH • BUSINESS', font=font_small, fill=(255, 210, 95, 255))

# Category badge.
rounded_box((55, 260, 390, 340), (0, 163, 230, 235), 20)
draw.text((85, 275), 'TECHNOLOGY', font=font_small, fill='white')

# Main headline card.
rounded_box((48, 920, 1032, 1450), (4, 13, 35, 225), 30)
draw.multiline_text((86, 985), 'បច្ចេកវិទ្យាឌីជីថល\nនិងហិរញ្ញវត្ថុ\nកំពុងរីកចម្រើន', font=font_big, fill='white', spacing=15)
draw.line((88, 1250, 350, 1250), fill=(255, 208, 80, 255), width=7)
draw.multiline_text((88, 1290), 'ព័ត៌មានសាកល្បងជាភាសាខ្មែរ\nសម្រាប់ short video reel', font=font_medium, fill=(210, 225, 245, 255), spacing=8)

# Bottom callout.
rounded_box((55, 1740, 1025, 1845), (0, 71, 125, 220), 22)
draw.text((90, 1760), 'Finance  •  Technology  •  Business', font=font_small, fill='white')

final_image = Image.alpha_composite(background.convert('RGBA'), overlay).convert('RGB')
poster = root / 'demo_reel_poster.jpg'
final_image.save(poster, quality=92, optimize=True)

video = root / 'demo_reel_khmer_voiceover.mp4'
audio = root / 'demo_reel_voiceover.wav'
cmd = [
    'ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', str(poster), '-i', str(audio),
    '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '128k',
    '-shortest', '-movflags', '+faststart', str(video)
]
subprocess.run(cmd, check=True, timeout=120)
print(video)
