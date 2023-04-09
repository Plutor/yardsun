#!/usr/bin/python3

import argparse
import datetime
import io
import logging
import math
import re
import sys
import os
from dateutil import tz
from itertools import chain
from libcamera import controls
from picamera2 import Picamera2, Preview
from suntime import Sun, SunTimeException
from wand.image import Image
from wand.drawing import Drawing

logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s] %(levelname)s - %(message)s',
)

now = datetime.datetime.now(tz=tz.tzlocal())
nowday = now.strftime('%Y%m%d')
nowtime = now.strftime('%H%M%S')

def load_or_take_photo(filename):
  if filename is None:
    logging.info('taking photo')
    img = take_photo()
  else:
    img = Image(filename=filename)
  logging.info(f'Loaded {img.width}x{img.height} file')
  return img

def take_photo():
  picam = Picamera2()
  picam.configure(picam.create_still_configuration())
  picam.set_controls({"AfMode": controls.AfModeEnum.Manual,
                      "LensPosition": 0.0,
                      "ExposureTime": 100, # usec
                      "AnalogueGain": 0.0,
                      "AeEnable": False,
                      "AwbEnable": False})
  photofile = os.path.join(photoroot, 'latest-photo.jpg')
  picam.start_and_capture_file(photofile, show_preview=False)
  img = Image(filename=photofile)
  # Rotate to portrait
  img.rotate(degree=90)
  return img

photoroot = os.path.join(os.path.dirname(__file__), 'photos')
def save_image(img, imgtype):
  f = os.path.join(photoroot, f'latest{imgtype}')
  logging.info(f'Saving {f}')
  img.save(filename=f)

  photodir = os.path.join(photoroot, nowday)
  try:
    os.mkdir(photodir)
  except FileExistsError:
    pass
  f = os.path.join(photodir, f'{nowtime}{imgtype}')
  logging.info(f'Saving {f}')
  img.save(filename=f)

src_points = ((75, 519), (269, 519), (610, 960), (0, 999))
dst_points = ((0, 0), (200, 0), (200, 800), (0, 800))
def fix_perspective(img):
  logging.info('fix_perspective')
  scale = 1000 / img.height
  img.resize(math.floor(img.width * scale), math.floor(img.height * scale))
  # Draw a polygon where the src_points are before saving.
  with img.clone() as scl:
    with Drawing() as draw:
      draw.stroke_width = 2
      draw.stroke_color = 'red'
      draw.fill_opacity = 0
      draw.polygon(list(src_points))
      draw(scl)
    save_image(scl, '-scaled.jpg')
  order = chain.from_iterable(zip(src_points, dst_points))
  arguments = list(chain.from_iterable(order))
  img.distort('perspective', arguments)
  img.crop(0, 0, 200, 800)
  save_image(img, '-flat.jpg')
  return img

def threshold(img):
  img.transform_colorspace('gray')
  img.black_threshold(threshold='#404040')
  img.white_threshold(threshold='#404040')
  return img

def sun_is_up():
  sun = Sun(args.lat, args.lng)
  sunrise = sun.get_local_sunrise_time()
  sunset = sun.get_local_sunset_time()
  logging.debug(f'sunrise={sunrise}, now={now}, sunset={sunset}')
  if now < sunrise:
    logging.info(f'Sun does not rise until {sunrise}')
    return False
  if now > sunset:
    logging.info(f'Sun went down at {sunset}')
    return False
  return True

def is_sunny(img):
  with img.clone() as c:
    img.transform_colorspace('gray')
    sunny = img.standard_deviation > args.min_stdev
    if not sunny:
      logging.info(f'Photo isn\'t sunny ({img.standard_deviation} < {args.min_stdev})')
    return sunny


########################################
# main

parser = argparse.ArgumentParser(
                    prog='yardsun',
                    description='Watches the backyard for sun')
parser.add_argument('-f', '--file')
parser.add_argument('--lat', default=42.33, type=float)  # Boston, MA
parser.add_argument('--lng', default=-71.03, type=float)
parser.add_argument('--min_stdev', default=7000, type=float)  # Based on trial and error
args = parser.parse_args()

if not sun_is_up():
  os.exit(0)

with load_or_take_photo(args.file) as orig:
  flat = fix_perspective(orig)
  if is_sunny(flat):
    vals = threshold(flat)
    save_image(vals, '.png')
