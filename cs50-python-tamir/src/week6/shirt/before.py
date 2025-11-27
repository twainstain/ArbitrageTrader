import sys
import os
from PIL import Image, ImageOps

try:
    if len(sys.argv) < 3:
        sys.exit("Too few command-line arguments")
    if len(sys.argv) > 3:
        sys.exit("Too many command-line arguments")
    read_image, write_image = sys.argv[1:]
    file ,read_image_ext = os.path.splitext(read_image)
        #read_image.lower().split('.')[-1]
    file, write_image_ext = os.path.splitext(write_image)
    if read_image_ext not in [".jpg", ".jpeg", ".png"] or write_image_ext not in [".jpg", ".jpeg", ".png"]:
        sys.exit("Invalid input")
    if read_image_ext != write_image_ext:
        sys.exit("Input and output have different extensions")
    shirt = Image.open("shirt.png")
    shirt_size = shirt.size
    before = Image.open(read_image)
    before = ImageOps.fit(before, shirt_size)
    before.paste(shirt, shirt)
    before.save(write_image)
except FileNotFoundError:
    sys.exit(f" Could not read {sys.argv[1]}")
