"""Вырезает льва со скриншота axlev.ru и делает слой с мягко растворяющимися краями."""
from PIL import Image, ImageChops, ImageDraw, ImageFilter

src = Image.open("site-screenshot.jpg").convert("RGB")
# область без меню, адреса и нижних надписей сайта
lion = src.crop((300, 90, 1640, 880))
w, h = lion.size

# маска: эллипс с сильно размытым краем
mask = Image.new("L", (w, h), 0)
ImageDraw.Draw(mask).ellipse((w * 0.1, h * 0.1, w * 0.9, h * 0.92), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(80))
# гарантированно прозрачные края, чтобы не было видно границ картинки
fade = Image.new("L", (w, h), 0)
ImageDraw.Draw(fade).rectangle((40, 40, w - 40, h - 40), fill=255)
mask = ImageChops.multiply(mask, fade.filter(ImageFilter.GaussianBlur(30)))

lion.putalpha(mask)
lion.save("lion-layer.png")
print(w, h)
