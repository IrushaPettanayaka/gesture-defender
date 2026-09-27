"""Generate an original procedural icon for the executable and installer."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
path = root / "art"
path.mkdir(exist_ok=True)
image = Image.new("RGBA", (256, 256), (8, 17, 31, 255))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((12, 12, 244, 244), radius=46, outline=(48, 113, 133), width=5)
draw.polygon([(128, 33), (48, 200), (112, 173)], fill=(32, 111, 137))
draw.polygon([(128, 33), (208, 200), (144, 173)], fill=(59, 197, 205))
draw.polygon([(128, 33), (112, 173), (128, 192), (144, 173)], fill=(160, 251, 237))
draw.polygon([(128, 92), (119, 144), (137, 144)], fill=(11, 38, 65))
draw.polygon([(118, 193), (128, 225), (138, 193)], fill=(255, 181, 119))
image.save(path / "game.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
image.save(path / "game.png")
