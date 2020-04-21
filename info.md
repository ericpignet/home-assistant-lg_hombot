# LG Hombot/Roboking Component for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz/)

The LG Hombot `vacuum` platform allows you to control the state of your LG Hombot robot vacuum.
This robot is also called Roboking in some countries.

You first have to plug a wifi dongle to your robot and [install Wifi support](https://www.roboter-forum.com/index.php?thread/10009-lg-hombot-3-0-wlan-kamera-steuerung-per-weboberfl%C3%A4che/&postID=107354#post107354) before it can be controlled by this platform.

You can display various data like the robot status or the charging level via template sensors. See the [README](https://github.com/ericpignet/home-assistant-lg_hombot/blob/master/README.md) for examples.

## Installation
Recommended: use [HACS](https://hacs.xyz/).

Manual: copy `custom_components/lg_hombot` folder into your `custom_components`.

## Configuration
```
vacuum:
  - platform: lg_hombot
    host: your_hombot_ip_address
    port: 6260
```

## Documentation
See [README](https://github.com/ericpignet/home-assistant-lg_hombot/blob/master/README.md) for full documentation.