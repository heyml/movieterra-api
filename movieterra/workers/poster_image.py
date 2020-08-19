import urllib
import PIL
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from io import BytesIO

from movieterra.common.utils import TEMPLATES_PATH

BASE_FONT_PATH = "movieterra/fonts/OpenSans.ttf"
NUMBER_FONT_PATH = "movieterra/fonts/opensans_semi_bold.ttf"
POSTERS_FOLDER = 'movieterra/static' 
SOURCE_URL = 'https://api.movieterra.com/'  #'http://127.0.0.1:5000'

translator = str.maketrans('', '', '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')

def create_local_poster(vkino_poster_url, month, day, filename):
    with urllib.request.urlopen(vkino_poster_url) as url:
        poster_file = BytesIO(url.read())
        img_poster = Image.open(poster_file)
    #poster_url = create_local_poster(img_poster, month, day, filename)
    max_poster_width  = 615
    max_poster_height = 230
    maxsize = (max_poster_width, max_poster_height)
    wpercent = (max_poster_width / float(img_poster.size[0]))
    hsize = int((float(img_poster.size[1]) * float(wpercent)))
    img_poster = img_poster.resize((max_poster_width, hsize), Image.ANTIALIAS)
    font_base_size = 12
    font_bigger_size = 26
    font_base = ImageFont.truetype(font = BASE_FONT_PATH, size = font_base_size)
    font_number = ImageFont.truetype(font = NUMBER_FONT_PATH, size = font_bigger_size)
    box_width = 79
    box_height = 65
    box_coordinates = (505, 0)
    padding_top = 5
    box_color = "rgb(255, 164, 57)"
    month = month.upper()

    day_padding_left = 10 if len(day) == 1 else 5
    print(month)
    month_padding_left = 12 if len(month) <= 7 else 0
    if len(month) == 5:
        print('sizhen')
        month_padding_left = 20    
    source_img = img_poster.convert("RGBA")

    box_img = Image.new('RGBA', (box_width, box_height), box_color)

    source_img.paste(box_img, box_coordinates)
    draw = ImageDraw.Draw(source_img)    
    draw.text((box_coordinates[0] + 7, padding_top), "ПРЕМ'ЄРА", font = font_base)
    draw.text((box_coordinates[0] + 20 + day_padding_left, 2 * padding_top + font_base_size / 2), day, font = font_number) 
    draw.text((box_coordinates[0] + month_padding_left, 2.5 * padding_top + font_base_size + font_bigger_size), month, font = font_base)
    draw.polygon([(box_coordinates[0], box_height), (box_coordinates[0]+box_width/2, box_width), (box_coordinates[0]+box_width, box_height)], fill = (255, 164, 57))
    button_img = Image.open('{}/buy-ticket.jpg'.format(TEMPLATES_PATH))
    source_img.paste(button_img, (20, 290))
    source_img.save('{}/'.format(POSTERS_FOLDER) + filename)
    return '{}/{}/'.format(SOURCE_URL, 'static') + filename
