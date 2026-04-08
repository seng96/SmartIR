import importlib.util
import json
import sys
import types
import unittest
from enum import IntFlag
from pathlib import Path
from unittest.mock import AsyncMock, call, patch


ROOT = Path(__file__).resolve().parents[1]


def _install_stubs():
    if "voluptuous" not in sys.modules:
        voluptuous = types.ModuleType("voluptuous")

        class DummySchema:
            def extend(self, value):
                return self

        voluptuous.Optional = lambda *args, **kwargs: None
        voluptuous.Required = lambda *args, **kwargs: None
        voluptuous.Schema = lambda *args, **kwargs: DummySchema()
        voluptuous.ALLOW_EXTRA = object()
        sys.modules["voluptuous"] = voluptuous

    if "aiofiles" not in sys.modules:
        aiofiles = types.ModuleType("aiofiles")
        sys.modules["aiofiles"] = aiofiles

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

    restore_state = types.ModuleType("homeassistant.helpers.restore_state")

    class RestoreEntity:
        async def async_added_to_hass(self):
            return None

        async def async_get_last_state(self):
            return None

    restore_state.RestoreEntity = RestoreEntity
    sys.modules["homeassistant.helpers.restore_state"] = restore_state

    climate = types.ModuleType("homeassistant.components.climate")

    class DummyPlatformSchema:
        def extend(self, value):
            return self

    class ClimateEntity:
        def async_write_ha_state(self):
            return None

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
    sys.modules["custom_components.smartir"] = smartir


def _load_climate_module():
    _install_stubs()
    for module_name in [
        "custom_components.smartir.controller",
        "custom_components.smartir.climate",
    ]:
        sys.modules.pop(module_name, None)

    climate_path = ROOT / "custom_components" / "smartir" / "climate.py"
    spec = importlib.util.spec_from_file_location(
        "custom_components.smartir.climate",
        climate_path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeState:
    def __init__(self, state):
        self.state = state


class FakeStates:
    def __init__(self, mapping=None):
        self._mapping = mapping or {}

    def get(self, entity_id):
        return self._mapping.get(entity_id)


class FakeUnits:
    temperature_unit = "C"


class FakeConfig:
    units = FakeUnits()


class FakeHass:
    def __init__(self, states=None):
        self.config = FakeConfig()
        self.states = FakeStates(states)


class FakeAsyncFile:
    def __init__(self, content):
        self._content = content

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def read(self):
        return self._content


class ClimatePowerPrimerTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.climate_module = _load_climate_module()

    def _device_data(self, include_on=True, include_off=True, include_power=False):
        data = {
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
                "cool": {
                    "auto": {
                        "24": "cool-24",
                    }
                },
            },
        }
        if include_on:
            data["commands"]["on"] = "power-on"
        if include_off:
            data["commands"]["off"] = "power-off"
        if include_power:
            data["commands"]["power"] = "power-toggle"
        return data

    def _config(self, power_sensor=None):
        return {
            self.climate_module.CONF_NAME: "Office AC",
            self.climate_module.CONF_DEVICE_CODE: 9999,
            self.climate_module.CONF_CONTROLLER_DATA: "remote.test",
            self.climate_module.CONF_DELAY: 0.5,
            self.climate_module.CONF_POWER_SENSOR: power_sensor,
            self.climate_module.CONF_POWER_SENSOR_RESTORE_STATE: False,
        }

    def _entity(self, device_data, power_sensor_state=None, hvac_mode=None):
        fake_controller = types.SimpleNamespace(send=AsyncMock())
        states = {}
        power_sensor = None
        if power_sensor_state is not None:
            power_sensor = "binary_sensor.ac_power"
            states[power_sensor] = FakeState(power_sensor_state)

        hass = FakeHass(states)
        with patch.object(
            self.climate_module,
            "get_controller",
            return_value=fake_controller,
        ):
            entity = self.climate_module.SmartIRClimate(
                hass,
                self._config(power_sensor=power_sensor),
                device_data,
            )

        entity._controller = fake_controller
        entity._target_temperature = 24
        entity._current_fan_mode = "auto"
        entity._hvac_mode = hvac_mode or self.climate_module.HVACMode.COOL
        return entity, fake_controller

    def test_power_cannot_be_combined_with_on_or_off(self):
        error = self.climate_module._get_command_configuration_error(
            {"power": "toggle", "off": "power-off"}
        )
        self.assertEqual(
            error,
            "`commands.power` cannot be combined with `commands.on` or `commands.off`",
        )

    async def test_async_setup_platform_rejects_invalid_command_configuration(self):
        device_data = self._device_data(include_on=False, include_off=True, include_power=True)
        async_add_entities = AsyncMock()
        config = self._config()

        with patch.object(self.climate_module.os.path, "isdir", return_value=True), \
             patch.object(self.climate_module.os.path, "exists", return_value=True), \
             patch.object(
                 self.climate_module.aiofiles,
                 "open",
                 return_value=FakeAsyncFile(json.dumps(device_data)),
                 create=True,
             ):
            await self.climate_module.async_setup_platform(
                FakeHass(),
                config,
                async_add_entities,
            )

        async_add_entities.assert_not_called()

    async def test_power_command_with_power_sensor_on_skips_primer(self):
        entity, controller = self._entity(
            self._device_data(include_on=False, include_off=False, include_power=True),
            power_sensor_state=self.climate_module.STATE_ON,
        )

        with patch.object(self.climate_module.asyncio, "sleep", AsyncMock()) as sleep_mock:
            await entity.send_command()

        self.assertEqual(controller.send.await_args_list, [call("cool-24")])
        sleep_mock.assert_not_awaited()

    async def test_power_command_with_power_sensor_off_sends_primer_then_target(self):
        entity, controller = self._entity(
            self._device_data(include_on=False, include_off=False, include_power=True),
            power_sensor_state=self.climate_module.STATE_OFF,
        )

        with patch.object(self.climate_module.asyncio, "sleep", AsyncMock()) as sleep_mock:
            await entity.send_command()

        self.assertEqual(
            controller.send.await_args_list,
            [call("power-toggle"), call("cool-24")],
        )
        sleep_mock.assert_awaited_once_with(0.5)

    async def test_power_command_with_internal_on_state_skips_primer(self):
        entity, controller = self._entity(
            self._device_data(include_on=False, include_off=False, include_power=True),
            power_sensor_state=None,
            hvac_mode=self.climate_module.HVACMode.COOL,
        )

        with patch.object(self.climate_module.asyncio, "sleep", AsyncMock()) as sleep_mock:
            await entity.send_command()

        self.assertEqual(controller.send.await_args_list, [call("cool-24")])
        sleep_mock.assert_not_awaited()

    async def test_legacy_behavior_still_sends_on_before_target(self):
        entity, controller = self._entity(
            self._device_data(),
            power_sensor_state=self.climate_module.STATE_ON,
        )

        with patch.object(self.climate_module.asyncio, "sleep", AsyncMock()) as sleep_mock:
            await entity.send_command()

        self.assertEqual(
            controller.send.await_args_list,
            [call("power-on"), call("cool-24")],
        )
        sleep_mock.assert_awaited_once_with(0.5)

    async def test_power_command_off_mode_when_on_sends_toggle(self):
        entity, controller = self._entity(
            self._device_data(include_on=False, include_off=False, include_power=True),
            power_sensor_state=self.climate_module.STATE_ON,
            hvac_mode=self.climate_module.HVACMode.OFF,
        )

        with patch.object(self.climate_module.asyncio, "sleep", AsyncMock()) as sleep_mock:
            await entity.send_command()

        self.assertEqual(controller.send.await_args_list, [call("power-toggle")])
        sleep_mock.assert_not_awaited()

    async def test_power_command_off_mode_when_already_off_skips_command(self):
        entity, controller = self._entity(
            self._device_data(include_on=False, include_off=False, include_power=True),
            power_sensor_state=self.climate_module.STATE_OFF,
            hvac_mode=self.climate_module.HVACMode.OFF,
        )

        with patch.object(self.climate_module.asyncio, "sleep", AsyncMock()) as sleep_mock:
            await entity.send_command()

        self.assertEqual(controller.send.await_args_list, [])
        sleep_mock.assert_not_awaited()

    async def test_legacy_off_mode_still_sends_off_command(self):
        entity, controller = self._entity(
            self._device_data(),
            power_sensor_state=self.climate_module.STATE_ON,
            hvac_mode=self.climate_module.HVACMode.OFF,
        )

        with patch.object(self.climate_module.asyncio, "sleep", AsyncMock()) as sleep_mock:
            await entity.send_command()

        self.assertEqual(controller.send.await_args_list, [call("power-off")])
        sleep_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
