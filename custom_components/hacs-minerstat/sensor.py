from homeassistant.helpers import entity
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from datetime import timedelta
import voluptuous as vol
import urllib.request, json
import homeassistant.helpers.config_validation as cv

__version__ = '1.1.2'

CONF_NAME = 'name'
CONF_ACCESS_KEY = 'access_key'
CONF_RIG_NAME = 'rig_name'
CONF_BASE_CURRENCY = 'base_currency'
CONF_REVENUE = 'revenue'

DEFAULT_NAME = 'Minerstat'
DEFAULT_CURRENCY = 'USD'
DEFAULT_REVENUE = 'usd_month'
DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)
SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_BASE_CURRENCY, default=DEFAULT_CURRENCY): cv.string,
    vol.Optional(CONF_REVENUE, default=DEFAULT_REVENUE): cv.string,
    vol.Required(CONF_ACCESS_KEY): str,
    vol.Required(CONF_RIG_NAME): str,

})


def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([Minerstat(hass, config)])


class Minerstat(entity.Entity):
    def __init__(self, hass, config):
        self.hass = hass
        self._config = config
        self._state = None
        self._unit = None
        self._revenue = None
        self._powercost = None
        self._powercons = None
        self._exchange = 1
        self.update()

    @property
    def name(self):
        return self._config[CONF_NAME]

    @property
    def icon(self):
        return 'mdi:ethereum'

    @property
    def state(self):
        return self._state

    def update(self):
        self._unit = self._config[CONF_BASE_CURRENCY].upper()

        req = urllib.request.Request(
            f'https://api.minerstat.com/v2/stats/{self._config[CONF_ACCESS_KEY]}/{self._config[CONF_RIG_NAME]}',
            headers={'User-Agent': "Home-assistant.io"})
        with urllib.request.urlopen(req) as url:
            data = json.loads(url.read().decode())
            self._revenue = data[self._config[CONF_RIG_NAME]]['revenue'][self._config[CONF_REVENUE]]
            self._powercost = data[self._config[CONF_RIG_NAME]]['info']['electricity']
            self._powercons = data[self._config[CONF_RIG_NAME]]['info']['consumption']
            self._powercons = data[self._config[CONF_RIG_NAME]]['info']['uptime']
            self._powercons = data[self._config[CONF_RIG_NAME]]['info']['status']
            self._powercons = data[self._config[CONF_RIG_NAME]]['info']['os']['localip']
            self._powercons = data[self._config[CONF_RIG_NAME]]['info']['os']['cpu_temp']
            self._powercons = data[self._config[CONF_RIG_NAME]]['hardware']
            self._powercons = data[self._config[CONF_RIG_NAME]]['mining']

        if self._config[CONF_BASE_CURRENCY] != 'USD':
            req = urllib.request.Request(
                f'https://api.exchangeratesapi.io/latest?base={self._unit}&symbols=USD',
                headers={'User-Agent': "Home-assistant.io"})
            with urllib.request.urlopen(req) as url:
                data = json.loads(url.read().decode())
                self._exchange = data['rates']['USD']

        if self._config[CONF_REVENUE] == 'usd_month':
            self._state = round((self._revenue / self._exchange) - (self._powercons / 1000 * self._powercost * 24 * 30), 3)
        elif self._config[CONF_REVENUE] == 'usd_week':
            self._state = round((self._revenue / self._exchange) - (self._powercons / 1000 * self._powercost * 24 * 7), 3)
        else:
            self._state = round((self._revenue / self._exchange) - (self._powercons / 1000 * self._powercost * 24), 3)

    @property
    def device_state_attributes(self):
        return {
            'unit_of_measurement': self._unit
        }
