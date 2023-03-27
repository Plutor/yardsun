# yardsun

Watches my backyard for which areas get the most sun

## Setup

```shell
$ apt update
$ apt upgrade
$ apt install libmagickwand-dev python3-picamera2 imagemagick
$ pip install Wand suntime
```

## Dependencies

* [suntime](https://github.com/SatAgro/suntime) for sunrise/sunset times
* [Wand](https://docs.wand-py.org/) ImageMagick Python API
* [picamera2](https://github.com/raspberrypi/picamera2) libcamera-based Raspberry Pi camera API
