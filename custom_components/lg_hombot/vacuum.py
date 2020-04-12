"""
Support for Wi-Fi enabled LG Hombot robot vacuum cleaner.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/vacuum.lg_hombot/
"""
import asyncio
import urllib.parse
import logging
import voluptuous as vol

import aiohttp
import async_timeout

from homeassistant.components.vacuum import (
    VacuumDevice, PLATFORM_SCHEMA, SUPPORT_BATTERY, SUPPORT_FAN_SPEED,
    SUPPORT_PAUSE, SUPPORT_RETURN_HOME, SUPPORT_SEND_COMMAND, SUPPORT_STATUS,
    SUPPORT_STOP, SUPPORT_TURN_OFF, SUPPORT_TURN_ON)
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_NAME)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

ATTR_STATE = 'JSON_ROBOT_STATE'
ATTR_BATTERY = 'JSON_BATTPERC'
ATTR_MODE = 'JSON_MODE'
ATTR_REPEAT = 'JSON_REPEAT'
ATTR_LAST_CLEAN = 'CLREC_LAST_CLEAN'
ATTR_TURBO = 'JSON_TURBO'

DEFAULT_NAME = 'Hombot'

ICON = 'mdi:robot-vacuum'
#ICON = 'mdi:roomba'
PLATFORM = 'lg_hombot'

FAN_SPEED_NORMAL = 'Normal'
FAN_SPEED_TURBO = 'Turbo'
FAN_SPEEDS = [FAN_SPEED_NORMAL, FAN_SPEED_TURBO]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PORT): cv.string,
}, extra=vol.ALLOW_EXTRA)

# Commonly supported features
SUPPORT_HOMBOT = SUPPORT_BATTERY | SUPPORT_PAUSE | SUPPORT_RETURN_HOME | \
                 SUPPORT_SEND_COMMAND | SUPPORT_STATUS | SUPPORT_STOP | \
                 SUPPORT_TURN_OFF | SUPPORT_TURN_ON | SUPPORT_FAN_SPEED


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the LG Hombot vacuum cleaner platform."""
    if PLATFORM not in hass.data:
        hass.data[PLATFORM] = {}

    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    name = config.get(CONF_NAME)

    _LOGGER.info("Creating LG Hombot object %s (%s:%s)",
                 name, host, port)
    #TODO Async
    #yield from hass.async_add_job(roomba.connect)
    hombot_vac = HombotVacuum(name, host, port)
    hass.data[PLATFORM][name] = hombot_vac

    async_add_devices([hombot_vac], update_before_add=True)


class HombotVacuum(VacuumDevice):
    """Representation of a Hombot vacuum cleaner robot."""

    def __init__(self, name, host, port):
        """Initialize the Hombot handler."""
        self._battery_level = None
        self._fan_speed = None
        self._is_on = False
        self._name = name
        self._state_attrs = {}
        self._status = None
        self._host = host
        self._port = port

    @property
    def supported_features(self):
        """Flag vacuum cleaner robot features that are supported."""
        return SUPPORT_HOMBOT

    @property
    def fan_speed(self):
        """Return the fan speed of the vacuum cleaner."""
        return self._fan_speed

    @property
    def fan_speed_list(self):
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return FAN_SPEEDS

    @property
    def battery_level(self):
        """Return the battery level of the vacuum cleaner."""
        return self._battery_level

    @property
    def status(self):
        """Return the status of the vacuum cleaner."""
        return self._status

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._is_on

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use for device."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @asyncio.coroutine
    def async_query(self, command):
        _LOGGER.debug('In async_query')
        try:
            websession = async_get_clientsession(self.hass)

            with async_timeout.timeout(10, loop=self.hass.loop):
                url = 'http://{}:{}/json.cgi?{}'.format(self._host, self._port, urllib.parse.quote(command, safe=':'))
                _LOGGER.debug(url)
                webresponse = yield from websession.get(url)
                response = yield from webresponse.read()
            return True
        except asyncio.TimeoutError:
            _LOGGER.error("LG Hombot timed out")
            return False
        except aiohttp.ClientError as error:
            _LOGGER.error("Error getting LG Hombot data: %s", error)
            return False

    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        """Turn the vacuum on."""
        is_on = yield from self.async_query('{"COMMAND":"CLEAN_START"}')
        if is_on:
            self._is_on = True

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        """Turn the vacuum off and return to home."""
        yield from self.async_return_to_base()

    @asyncio.coroutine
    def async_stop(self, **kwargs):
        """Stop the vacuum cleaner."""
        yield from self.async_pause()

    @asyncio.coroutine
    def async_pause(self, **kwargs):
        """Pause the cleaning cycle."""
        is_off = yield from self.async_query('{"COMMAND":"PAUSE"}')
        if is_off:
            self._is_on = False

    @asyncio.coroutine
    def async_start_pause(self, **kwargs):
        """Pause the cleaning task or resume it."""
        if self.is_on:
            yield from self.async_pause()
        else:  # vacuum is off or paused
            yield from self.async_turn_on()

    @asyncio.coroutine
    def async_return_to_base(self, **kwargs):
        """Set the vacuum cleaner to return to the dock."""
        is_on = yield from self.async_query('{"COMMAND":"HOMING"}')
        if is_on:
            self._is_on = False

    @asyncio.coroutine
    def async_toggle_turbo(self, **kwargs):
        """Toggle between normal and turbo mode."""
        _LOGGER.debug('In toggle')
        yield from self.async_query('turbo')

    @asyncio.coroutine
    def async_set_fan_speed(self, fan_speed, **kwargs):
        """Set fan speed."""
        if fan_speed.capitalize() in FAN_SPEEDS:
            fan_speed = fan_speed.capitalize()
            _LOGGER.debug("Set fan speed to: %s", fan_speed)
            if fan_speed == FAN_SPEED_NORMAL:
                if self._fan_speed == FAN_SPEED_TURBO:
                    yield from self.async_toggle_turbo()
            elif fan_speed == FAN_SPEED_TURBO:
                if self._fan_speed == FAN_SPEED_NORMAL:
                    yield from self.async_toggle_turbo()
            self._fan_speed = fan_speed
        else:
            _LOGGER.error("No such fan speed available: %s", fan_speed)
            return

    @asyncio.coroutine
    def async_send_command(self, command, params, **kwargs):
        """Send raw command."""
        _LOGGER.debug("async_send_command %s", command)
        yield from self.query(command)
        return True

    @asyncio.coroutine
    def async_update(self):
        """Fetch state from the device."""
        response = ''
        try:
            websession = async_get_clientsession(self.hass)

            with async_timeout.timeout(10, loop=self.hass.loop):
                url = 'http://{}:{}/status.txt'.format(self._host, self._port)
                webresponse = yield from websession.get(url)
                bytesresponse = yield from webresponse.read()
                response = bytesresponse.decode('ascii')
                if len(response) == 0:
                    return False
        except asyncio.TimeoutError:
            _LOGGER.error("LG Hombot timed out")
            return False
        except aiohttp.ClientError as error:
            _LOGGER.error("Error getting LG Hombot data: %s", error)
            return False

        _LOGGER.debug(response)
        all_attrs = {}
        for line in response.splitlines():
            name, var = line.partition("=")[::2]
            all_attrs[name] = var.strip('"')

        self._status = all_attrs[ATTR_STATE]
        _LOGGER.debug("Got new state from the vacuum: %s", self._status)

        self._battery_level = int(all_attrs[ATTR_BATTERY])
        self._is_on = self._status in ['WORKING', 'BACKMOVING_INIT']
        self._fan_speed = FAN_SPEED_TURBO if all_attrs[ATTR_TURBO] == 'true' else FAN_SPEED_NORMAL
        self._state_attrs[ATTR_MODE] = all_attrs[ATTR_MODE]
        self._state_attrs[ATTR_REPEAT] = all_attrs[ATTR_REPEAT]
        self._state_attrs[ATTR_LAST_CLEAN] = all_attrs[ATTR_LAST_CLEAN]