#!/usr/bin/python3

import argparse
import datetime
import io
import logging
import math
import re
import sys
import os
from itertools import chain
from libcamera import controls
from picamera2 import Picamera2, Preview
from wand.image import Image

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
)

now = datetime.datetime.now()
nowday = now.strftime('%Y%m%d')
nowtime = now.strftime('%H%M%S')
photoroot = os.path.join(os.path.dirname(__file__), 'photos')

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
  picam.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0})
  photofile = os.path.join(photoroot, 'latest_photo.jpg')
  picam.start_and_capture_file(photofile, show_preview=False)
  img = Image(filename=photofile)
  # Rotate to portrait
  img.rotate(degree=90)
  return img

src_points = ((203, 328), (402, 332), (750, 701), (137, 740))
dst_points = ((0, 0), (200, 0), (200, 800), (0, 800))
def fix_perspective(img):
  logging.info('fix_perspective')
  scale = 1000 / img.height
  img.resize(math.floor(img.width * scale), math.floor(img.height * scale))
  # TODO: Draw a polygon where the src_points are before saving.
  img.save(filename=os.path.join(photoroot, 'latest_scaled.jpg'))
  order = chain.from_iterable(zip(src_points, dst_points))
  arguments = list(chain.from_iterable(order))
  img.distort('perspective', arguments)
  img.crop(0, 0, 200, 800)
  img.save(filename=os.path.join(photoroot, 'latest_flat.jpg'))
  return img

def threshold(img):
  img.transform_colorspace('gray')
  img.black_threshold(threshold='#666')
  img.white_threshold(threshold='#666')
  img.save(filename=os.path.join(photoroot, 'latest_threshold.png'))
  return img

def save_latest(img):
  img.save(filename=os.path.join(photoroot, 'latest.jpg'))
  photodir = os.path.join(photoroot, nowday)
  try:
    os.mkdir(photodir)
  except FileExistsError:
    pass
  photofile = os.path.join(photodir, f'{nowtime}.png')
  logging.info(f'Saving {photofile}')
  img.save(filename=photofile)

def update_averages(day):
  logging.info('update_averages')
  photodir = os.path.join(photoroot, day)
  # Open every png, for each pixel average how many are white.
  imgs = []
  for photofile in os.listdir(photodir):
    if not re.fullmatch(r'\d{6}\.png', photofile):
      continue
    imgs.append(Image(filename=os.path.join(photodir, photofile)))
  num = len(imgs)
  blendperc = '{:.0f}'.format(100/len(imgs))
  logging.info(blendperc)
  with imgs.pop() as avg:
    for img in imgs:
      avg.composite(img, operator='blend', arguments=blendperc)
    # avg.merge_layers(method='merge')
    avgfile = os.path.join(photodir, 'average.png')
    logging.info(f'Averaging {num} photos into {avgfile}')
    avg.save(filename=avgfile)

########################################
# main

parser = argparse.ArgumentParser(
                    prog='yardsun',
                    description='Watches the backyard for sun')
parser.add_argument('-f', '--file')
args = parser.parse_args()

with load_or_take_photo(args.file) as orig:
  flat = fix_perspective(orig)
  vals = threshold(flat)

  save_latest(vals)

update_averages(nowday)

