# yardsun

Watches my backyard for which areas get the most sun, and generates [summaries like this](https://imgur.com/r3gQUbP).
(TODO: Update this example gif once the leaves come in.)

## Setup

```shell
$ apt update
$ apt upgrade
$ apt install libmagickwand-dev python3-picamera2 imagemagick
$ pip install Wand suntime
```

Setup your crontab (`crontab -e`):

```
*/5 * * * *     /home/pi/yardsun/yardsun.py >> /home/pi/yardsun/yardsun.log 2>&1
0 21 * * *      /home/pi/yardsun/mksummary.sh
@reboot         cd /home/pi/yardsun && python -m http.server 8000
```

## Dependencies

* [suntime](https://github.com/SatAgro/suntime) for sunrise/sunset times
* [Wand](https://docs.wand-py.org/) ImageMagick Python API
* [picamera2](https://github.com/raspberrypi/picamera2) libcamera-based Raspberry Pi camera API
