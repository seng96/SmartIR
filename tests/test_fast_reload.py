import importlib.util
import json
import sys
import types
import unittest
from enum import IntFlag
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def _clear_modules(*module_names):
    for module_name in module_names:
        sys.modules.pop(module_name, None)


def _install_common_stubs():
    if "voluptuous" not in sys.modules:
        voluptuous = types.ModuleType("voluptuous")

        class DummySchema:
            def extend(self, value):
                return self

        voluptuous.Optional = lambda *args, **kwargs: None
        voluptuous.Required = lambda *args, **kwargs: None
        voluptuous.Schema = lambda *args, **kwargs: DummySchema()
        voluptuous.ALLOW_EXTRA = object()
        voluptuous.In = lambda *args, **kwargs: None
        sys.modules["voluptuous"] = voluptuous
    else:
        voluptuous = sys.modules["voluptuous"]
        if not hasattr(voluptuous, "In"):
            voluptuous.In = lambda *args, **kwargs: None

    if "aiofiles" not in sys.modules:
        sys.modules["aiofiles"] = types.ModuleType("aiofiles")

    if "aiohttp" not in sys.modules:
        aiohttp = types.ModuleType("aiohttp")
        aiohttp.ClientSession = object
        sys.modules["aiohttp"] = aiohttp

    if "requests" not in sys.modules:
        sys.modules["requests"] = types.ModuleType("requests")

    homeassistant = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = homeassistant

    const = types.ModuleType("homeassistant.const")
    const.CONF_NAME = "name"
    const.STATE_ON = "on"
    const.STATE_OFF = "off"
    const.STATE_UNKNOWN = "unknown"
    const.STATE_UNAVAILABLE = "unavailable"
    const.ATTR_TEMPERATURE = "temperature"
    const.PRECISION_TENTHS = 0.1
    const.PRECISION_HALVES = 0.5
    const.PRECISION_WHOLE = 1
    const.ATTR_ENTITY_ID = "entity_id"
    const.ATTR_FRIENDLY_NAME = "friendly_name"
    const.__version__ = "2025.5.0"
    sys.modules["homeassistant.const"] = const

    core = types.ModuleType("homeassistant.core")

    class _Event:
        def __class_getitem__(cls, item):
            return cls

    class _EventStateChangedData:
        pass

    core.Event = _Event
    core.EventStateChangedData = _EventStateChangedData
    core.callback = lambda func: func
    sys.modules["homeassistant.core"] = core

    helpers = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"] = helpers

    event = types.ModuleType("homeassistant.helpers.event")
    event.async_track_state_change = lambda *args, **kwargs: None
    event.async_track_state_change_event = lambda *args, **kwargs: None
    sys.modules["homeassistant.helpers.event"] = event

    config_validation = types.ModuleType("homeassistant.helpers.config_validation")
    config_validation.string = object()
    config_validation.positive_int = object()
    config_validation.positive_float = object()
    config_validation.entity_id = object()
    config_validation.boolean = object()
    sys.modules["homeassistant.helpers.config_validation"] = config_validation

    typing_mod = types.ModuleType("homeassistant.helpers.typing")
    typing_mod.ConfigType = dict
    sys.modules["homeassistant.helpers.typing"] = typing_mod

    restore_state = types.ModuleType("homeassistant.helpers.restore_state")

    class RestoreEntity:
        def __init__(self, *args, **kwargs):
            self._remove_callbacks = []

        async def async_added_to_hass(self):
            return None

        async def async_get_last_state(self):
            return None

        def async_on_remove(self, callback):
            if not hasattr(self, "_remove_callbacks"):
                self._remove_callbacks = []
            self._remove_callbacks.append(callback)

    restore_state.RestoreEntity = RestoreEntity
    sys.modules["homeassistant.helpers.restore_state"] = restore_state

    reload_mod = types.ModuleType("homeassistant.helpers.reload")

    async def async_setup_reload_service(*args, **kwargs):
        return None

    reload_mod.async_setup_reload_service = async_setup_reload_service
    sys.modules["homeassistant.helpers.reload"] = reload_mod

    custom_components = types.ModuleType("custom_components")
    custom_components.__path__ = [str(ROOT / "custom_components")]
    sys.modules["custom_components"] = custom_components

    smartir = types.ModuleType("custom_components.smartir")
    smartir.__path__ = [str(ROOT / "custom_components" / "smartir")]
    smartir.COMPONENT_ABS_DIR = str(ROOT / "custom_components" / "smartir")

    class Helper:
        @staticmethod
        async def downloader(source, dest):
            raise NotImplementedError

    smartir.Helper = Helper
    smartir.COMPONENT_ABS_DIR = str(ROOT / "custom_components" / "smartir")

    def get_device_files_absdir(platform):
        component_codes_dir = str(
            ROOT / "custom_components" / "smartir" / "codes" / platform
        )
        repo_codes_dir = str(ROOT / "codes" / platform)

        import os

        if os.path.isdir(component_codes_dir):
            return component_codes_dir

        if os.path.isdir(repo_codes_dir):
            return repo_codes_dir

        return component_codes_dir

    smartir.get_device_files_absdir = get_device_files_absdir
    sys.modules["custom_components.smartir"] = smartir


def _install_climate_stubs():
    climate = types.ModuleType("homeassistant.components.climate")

    class DummyPlatformSchema:
        def extend(self, value):
            return self

    class ClimateEntity:
        def async_write_ha_state(self):
            return None

        def async_on_remove(self, callback):
            if not hasattr(self, "_remove_callbacks"):
                self._remove_callbacks = []
            self._remove_callbacks.append(callback)

    climate.ClimateEntity = ClimateEntity
    climate.PLATFORM_SCHEMA = DummyPlatformSchema()
    sys.modules["homeassistant.components.climate"] = climate

    climate_const = types.ModuleType("homeassistant.components.climate.const")

    class ClimateEntityFeature(IntFlag):
        TURN_OFF = 1
        TURN_ON = 2
        TARGET_TEMPERATURE = 4
        FAN_MODE = 8
        SWING_MODE = 16

    class HVACMode:
        OFF = "off"
        COOL = "cool"
        HEAT = "heat"
        HEAT_COOL = "heat_cool"
        DRY = "dry"
        FAN_ONLY = "fan_only"
        AUTO = "auto"

    climate_const.ClimateEntityFeature = ClimateEntityFeature
    climate_const.HVACMode = HVACMode
    climate_const.HVAC_MODES = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.HEAT_COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.AUTO,
    ]
    climate_const.ATTR_HVAC_MODE = "hvac_mode"
    sys.modules["homeassistant.components.climate.const"] = climate_const


def _install_fan_stubs():
    fan = types.ModuleType("homeassistant.components.fan")

    class DummyPlatformSchema:
        def extend(self, value):
            return self

    class FanEntity:
        def async_write_ha_state(self):
            return None

        def async_on_remove(self, callback):
            if not hasattr(self, "_remove_callbacks"):
                self._remove_callbacks = []
            self._remove_callbacks.append(callback)

    class FanEntityFeature(IntFlag):
        SET_SPEED = 1
        TURN_OFF = 2
        TURN_ON = 4
        DIRECTION = 8
        OSCILLATE = 16

    fan.FanEntity = FanEntity
    fan.FanEntityFeature = FanEntityFeature
    fan.PLATFORM_SCHEMA = DummyPlatformSchema()
    fan.DIRECTION_REVERSE = "reverse"
    fan.DIRECTION_FORWARD = "forward"
    sys.modules["homeassistant.components.fan"] = fan

    util_percentage = types.ModuleType("homeassistant.util.percentage")
    util_percentage.ordered_list_item_to_percentage = lambda items, item: 50
    util_percentage.percentage_to_ordered_list_item = lambda items, pct: items[0]
    sys.modules["homeassistant.util.percentage"] = util_percentage


def _install_light_stubs():
    light = types.ModuleType("homeassistant.components.light")

    class DummyPlatformSchema:
        def extend(self, value):
            return self

    class LightEntity:
        def async_write_ha_state(self):
            return None

        def async_on_remove(self, callback):
            if not hasattr(self, "_remove_callbacks"):
                self._remove_callbacks = []
            self._remove_callbacks.append(callback)

    class ColorMode:
        UNKNOWN = "unknown"
        COLOR_TEMP = "color_temp"
        BRIGHTNESS = "brightness"
        ONOFF = "onoff"

    light.ATTR_BRIGHTNESS = "brightness"
    light.ATTR_COLOR_TEMP_KELVIN = "color_temp_kelvin"
    light.ColorMode = ColorMode
    light.LightEntity = LightEntity
    light.PLATFORM_SCHEMA = DummyPlatformSchema()
    sys.modules["homeassistant.components.light"] = light


def _install_media_player_stubs():
    media_player = types.ModuleType("homeassistant.components.media_player")

    class DummyPlatformSchema:
        def extend(self, value):
            return self

    class MediaPlayerEntity:
        def async_write_ha_state(self):
            return None

    media_player.MediaPlayerEntity = MediaPlayerEntity
    media_player.PLATFORM_SCHEMA = DummyPlatformSchema()
    sys.modules["homeassistant.components.media_player"] = media_player

    media_player_const = types.ModuleType("homeassistant.components.media_player.const")

    class MediaPlayerEntityFeature(IntFlag):
        TURN_OFF = 1
        TURN_ON = 2
        PREVIOUS_TRACK = 4
        NEXT_TRACK = 8
        VOLUME_STEP = 16
        VOLUME_MUTE = 32
        SELECT_SOURCE = 64
        PLAY_MEDIA = 128

    class MediaType:
        CHANNEL = "channel"

    media_player_const.MediaPlayerEntityFeature = MediaPlayerEntityFeature
    media_player_const.MediaType = MediaType
    sys.modules["homeassistant.components.media_player.const"] = media_player_const


def _load_module(module_name, relative_path):
    _clear_modules(module_name, "custom_components.smartir.controller")
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class FakeUnits:
    temperature_unit = "C"


class FakeConfig:
    units = FakeUnits()


class FakeState:
    def __init__(self, state, attributes=None):
        self.state = state
        self.attributes = attributes or {}


class FakeStates:
    def __init__(self, mapping=None):
        self._mapping = mapping or {}

    def get(self, entity_id):
        return self._mapping.get(entity_id)


class FakeServices:
    def __init__(self):
        self.async_register = Mock()


class FakeHass:
    def __init__(self, states=None):
        self.config = FakeConfig()
        self.states = FakeStates(states)
        self.services = FakeServices()


class FakeAsyncFile:
    def __init__(self, content):
        self._content = content

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def read(self):
        return self._content


class SmartIRReloadSetupTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        _install_common_stubs()
        cls.init_module = _load_module(
            "custom_components.smartir.__init__",
            "custom_components/smartir/__init__.py",
        )

    async def test_async_setup_registers_reload_service_for_all_platforms(self):
        hass = FakeHass()
        config = {
            self.init_module.DOMAIN: {
                self.init_module.CONF_CHECK_UPDATES: False,
                self.init_module.CONF_UPDATE_BRANCH: "master",
            }
        }

        with patch.object(
            self.init_module,
            "async_setup_reload_service",
            AsyncMock(),
            create=True,
        ) as reload_service:
            await self.init_module.async_setup(hass, config)

        reload_service.assert_awaited_once_with(
            hass,
            self.init_module.DOMAIN,
            ["climate", "fan", "light", "media_player"],
        )

    async def test_async_setup_registers_reload_service_without_root_config(self):
        hass = FakeHass()

        with patch.object(
            self.init_module,
            "async_setup_reload_service",
            AsyncMock(),
            create=True,
        ) as reload_service:
            result = await self.init_module.async_setup(hass, {})

        self.assertTrue(result)
        reload_service.assert_awaited_once_with(
            hass,
            self.init_module.DOMAIN,
            ["climate", "fan", "light", "media_player"],
        )


class SmartIRListenerLifecycleTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        _install_common_stubs()
        _install_climate_stubs()
        _install_fan_stubs()
        _install_light_stubs()
        _install_media_player_stubs()
        cls.climate_module = _load_module(
            "custom_components.smartir.climate",
            "custom_components/smartir/climate.py",
        )
        cls.fan_module = _load_module(
            "custom_components.smartir.fan",
            "custom_components/smartir/fan.py",
        )
        cls.light_module = _load_module(
            "custom_components.smartir.light",
            "custom_components/smartir/light.py",
        )
        cls.media_player_module = _load_module(
            "custom_components.smartir.media_player",
            "custom_components/smartir/media_player.py",
        )

    def _climate_config(self):
        return {
            self.climate_module.CONF_NAME: "Office AC",
            self.climate_module.CONF_DEVICE_CODE: 9999,
            self.climate_module.CONF_CONTROLLER_DATA: "remote.office",
            self.climate_module.CONF_DELAY: 0.5,
            self.climate_module.CONF_TEMPERATURE_SENSOR: "sensor.temp",
            self.climate_module.CONF_HUMIDITY_SENSOR: "sensor.humidity",
            self.climate_module.CONF_POWER_SENSOR: "binary_sensor.power",
            self.climate_module.CONF_POWER_SENSOR_RESTORE_STATE: False,
        }

    def _climate_device_data(self):
        return {
            "manufacturer": "Test",
            "supportedModels": ["Model"],
            "supportedController": "Broadlink",
            "commandsEncoding": "Base64",
            "minTemperature": 16,
            "maxTemperature": 30,
            "precision": 1,
            "operationModes": ["cool"],
            "fanModes": ["auto"],
            "commands": {
                "on": "power-on",
                "off": "power-off",
                "cool": {"auto": {"24": "cool-24"}},
            },
        }

    def _fan_config(self):
        return {
            self.fan_module.CONF_NAME: "Office Fan",
            self.fan_module.CONF_DEVICE_CODE: 1000,
            self.fan_module.CONF_CONTROLLER_DATA: "remote.office",
            self.fan_module.CONF_DELAY: 0.5,
            self.fan_module.CONF_POWER_SENSOR: "binary_sensor.fan_power",
        }

    def _fan_device_data(self):
        return {
            "manufacturer": "Test",
            "supportedModels": ["Model"],
            "supportedController": "Broadlink",
            "commandsEncoding": "Base64",
            "speed": ["low", "medium", "high"],
            "commands": {"low": "low-code", "medium": "med-code", "high": "hi-code"},
        }

    def _light_config(self):
        return {
            self.light_module.CONF_NAME: "Office Light",
            self.light_module.CONF_DEVICE_CODE: 1000,
            self.light_module.CONF_CONTROLLER_DATA: "remote.office",
            self.light_module.CONF_DELAY: 0.5,
            self.light_module.CONF_POWER_SENSOR: "binary_sensor.light_power",
        }

    def _light_device_data(self):
        return {
            "manufacturer": "Test",
            "supportedModels": ["Model"],
            "supportedController": "Broadlink",
            "commandsEncoding": "Base64",
            "brightness": [25, 50, 75, 100],
            "colorTemperature": [2700, 4000, 6500],
            "commands": {
                "on": "on-code",
                "off": "off-code",
                "brighten": "bright-code",
                "dim": "dim-code",
            },
        }

    def _media_player_config(self):
        return {
            self.media_player_module.CONF_NAME: "Office TV",
            self.media_player_module.CONF_DEVICE_CODE: 1000,
            self.media_player_module.CONF_CONTROLLER_DATA: "remote.office",
            self.media_player_module.CONF_DELAY: 0.5,
            self.media_player_module.CONF_DEVICE_CLASS: "tv",
        }

    def _media_player_device_data(self):
        return {
            "manufacturer": "Test",
            "supportedModels": ["Model"],
            "supportedController": "Broadlink",
            "commandsEncoding": "Base64",
            "commands": {
                "on": "on-code",
                "off": "off-code",
            },
        }

    async def test_climate_registers_listener_unsubscribers_on_remove(self):
        hass = FakeHass(
            {
                "sensor.temp": FakeState("24"),
                "sensor.humidity": FakeState("50"),
                "binary_sensor.power": FakeState(self.climate_module.STATE_ON),
            }
        )
        entity = self.climate_module.SmartIRClimate(
            hass,
            self._climate_config(),
            self._climate_device_data(),
        )

        with patch.object(
            self.climate_module,
            "async_track_state_change_event",
            side_effect=[object(), object(), object()],
        ) as track_mock:
            await entity.async_added_to_hass()

        self.assertEqual(track_mock.call_count, 3)
        self.assertEqual(len(getattr(entity, "_remove_callbacks", [])), 3)

    async def test_climate_setup_platform_rereads_device_json_on_each_setup(self):
        hass = FakeHass()
        config = self._climate_config()
        json_v1 = self._climate_device_data()
        json_v2 = self._climate_device_data()
        json_v2["manufacturer"] = "Updated"

        with patch.object(self.climate_module.os.path, "isdir", return_value=True), \
             patch.object(self.climate_module.os.path, "exists", return_value=True), \
             patch.object(
                 self.climate_module.aiofiles,
                 "open",
                 side_effect=[
                     FakeAsyncFile(json.dumps(json_v1)),
                     FakeAsyncFile(json.dumps(json_v2)),
                 ],
                 create=True,
             ), \
             patch.object(self.climate_module, "SmartIRClimate", side_effect=["entity-v1", "entity-v2"]) as entity_cls:
            async_add_entities = Mock()
            await self.climate_module.async_setup_platform(hass, config, async_add_entities)
            await self.climate_module.async_setup_platform(hass, config, async_add_entities)

        self.assertEqual(entity_cls.call_args_list[0].args[2]["manufacturer"], "Test")
        self.assertEqual(entity_cls.call_args_list[1].args[2]["manufacturer"], "Updated")

    def test_fan_device_files_dir_prefers_repo_codes_when_component_codes_missing(self):
        component_codes_dir = ROOT / "custom_components" / "smartir" / "codes" / "fan"
        repo_codes_dir = ROOT / "codes" / "fan"

        def fake_isdir(path):
            return path == str(repo_codes_dir)

        with patch.object(self.fan_module.os.path, "isdir", side_effect=fake_isdir):
            device_dir = self.fan_module.get_device_files_absdir("fan")

        self.assertEqual(device_dir, str(repo_codes_dir))

    async def test_fan_setup_platform_rereads_device_json_on_each_setup(self):
        hass = FakeHass()
        config = self._fan_config()
        json_v1 = self._fan_device_data()
        json_v2 = self._fan_device_data()
        json_v2["manufacturer"] = "Updated"

        with patch.object(self.fan_module.os.path, "isdir", return_value=True), \
             patch.object(self.fan_module.os.path, "exists", return_value=True), \
             patch.object(
                 self.fan_module.aiofiles,
                 "open",
                 side_effect=[
                     FakeAsyncFile(json.dumps(json_v1)),
                     FakeAsyncFile(json.dumps(json_v2)),
                 ],
                 create=True,
             ), \
             patch.object(self.fan_module, "SmartIRFan", side_effect=["entity-v1", "entity-v2"]) as entity_cls:
            async_add_entities = Mock()
            await self.fan_module.async_setup_platform(hass, config, async_add_entities)
            await self.fan_module.async_setup_platform(hass, config, async_add_entities)

        self.assertEqual(entity_cls.call_args_list[0].args[2]["manufacturer"], "Test")
        self.assertEqual(entity_cls.call_args_list[1].args[2]["manufacturer"], "Updated")

    async def test_fan_registers_power_listener_even_without_restore_state(self):
        hass = FakeHass()
        entity = self.fan_module.SmartIRFan(
            hass,
            self._fan_config(),
            self._fan_device_data(),
        )

        with patch.object(
            self.fan_module,
            "async_track_state_change_event",
            return_value=object(),
        ) as track_mock:
            await entity.async_added_to_hass()

        track_mock.assert_called_once_with(
            hass,
            "binary_sensor.fan_power",
            entity._async_power_sensor_changed,
        )
        self.assertEqual(len(getattr(entity, "_remove_callbacks", [])), 1)

    async def test_light_registers_listener_unsubscriber_on_remove(self):
        hass = FakeHass()
        entity = self.light_module.SmartIRLight(
            hass,
            self._light_config(),
            self._light_device_data(),
        )

        with patch.object(
            self.light_module,
            "async_track_state_change_event",
            return_value=object(),
        ) as track_mock:
            await entity.async_added_to_hass()

        track_mock.assert_called_once_with(
            hass,
            "binary_sensor.light_power",
            entity._async_power_sensor_changed,
        )
        self.assertEqual(len(getattr(entity, "_remove_callbacks", [])), 1)

    def test_light_device_files_dir_prefers_repo_codes_when_component_codes_missing(self):
        component_codes_dir = ROOT / "custom_components" / "smartir" / "codes" / "light"
        repo_codes_dir = ROOT / "codes" / "light"

        def fake_isdir(path):
            return path == str(repo_codes_dir)

        with patch.object(self.light_module.os.path, "isdir", side_effect=fake_isdir):
            device_dir = self.light_module.get_device_files_absdir("light")

        self.assertEqual(device_dir, str(repo_codes_dir))

    async def test_light_setup_platform_rereads_device_json_on_each_setup(self):
        hass = FakeHass()
        config = self._light_config()
        json_v1 = self._light_device_data()
        json_v2 = self._light_device_data()
        json_v2["manufacturer"] = "Updated"

        with patch.object(self.light_module.os.path, "isdir", return_value=True), \
             patch.object(self.light_module.os.path, "exists", return_value=True), \
             patch.object(
                 self.light_module.aiofiles,
                 "open",
                 side_effect=[
                     FakeAsyncFile(json.dumps(json_v1)),
                     FakeAsyncFile(json.dumps(json_v2)),
                 ],
                 create=True,
             ), \
             patch.object(self.light_module, "SmartIRLight", side_effect=["entity-v1", "entity-v2"]) as entity_cls:
            async_add_entities = Mock()
            await self.light_module.async_setup_platform(hass, config, async_add_entities)
            await self.light_module.async_setup_platform(hass, config, async_add_entities)

        self.assertEqual(entity_cls.call_args_list[0].args[2]["manufacturer"], "Test")
        self.assertEqual(entity_cls.call_args_list[1].args[2]["manufacturer"], "Updated")

    def test_media_player_device_files_dir_prefers_repo_codes_when_component_codes_missing(self):
        component_codes_dir = ROOT / "custom_components" / "smartir" / "codes" / "media_player"
        repo_codes_dir = ROOT / "codes" / "media_player"

        def fake_isdir(path):
            return path == str(repo_codes_dir)

        with patch.object(self.media_player_module.os.path, "isdir", side_effect=fake_isdir):
            device_dir = self.media_player_module.get_device_files_absdir("media_player")

        self.assertEqual(device_dir, str(repo_codes_dir))

    async def test_media_player_setup_platform_rereads_device_json_on_each_setup(self):
        hass = FakeHass()
        config = self._media_player_config()
        json_v1 = self._media_player_device_data()
        json_v2 = self._media_player_device_data()
        json_v2["manufacturer"] = "Updated"

        with patch.object(self.media_player_module.os.path, "isdir", return_value=True), \
             patch.object(self.media_player_module.os.path, "exists", return_value=True), \
             patch.object(
                 self.media_player_module.aiofiles,
                 "open",
                 side_effect=[
                     FakeAsyncFile(json.dumps(json_v1)),
                     FakeAsyncFile(json.dumps(json_v2)),
                 ],
                 create=True,
             ), \
             patch.object(
                 self.media_player_module,
                 "SmartIRMediaPlayer",
                 side_effect=["entity-v1", "entity-v2"],
             ) as entity_cls:
            async_add_entities = Mock()
            await self.media_player_module.async_setup_platform(hass, config, async_add_entities)
            await self.media_player_module.async_setup_platform(hass, config, async_add_entities)

        self.assertEqual(entity_cls.call_args_list[0].args[2]["manufacturer"], "Test")
        self.assertEqual(entity_cls.call_args_list[1].args[2]["manufacturer"], "Updated")
