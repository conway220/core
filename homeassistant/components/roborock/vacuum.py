"""Support for Roborock vacuum class."""
from abc import ABC
from typing import Any

from roborock.code_mappings import FAN_SPEED_CODES
from roborock.typing import RoborockCommand, RoborockDeviceInfo

from homeassistant.components.vacuum import (
    ATTR_BATTERY_ICON,
    ATTR_FAN_SPEED,
    ATTR_FAN_SPEED_LIST,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_BATTERY_LEVEL, ATTR_STATE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from . import RoborockDataUpdateCoordinator
from .const import DOMAIN
from .device import RoborockCoordinatedEntity

STATE_CODE_TO_STATE = {
    1: STATE_IDLE,  # "Starting"
    2: STATE_IDLE,  # "Charger disconnected"
    3: STATE_IDLE,  # "Idle"
    4: STATE_CLEANING,  # "Remote control active"
    5: STATE_CLEANING,  # "Cleaning"
    6: STATE_RETURNING,  # "Returning home"
    7: STATE_CLEANING,  # "Manual mode"
    8: STATE_DOCKED,  # "Charging"
    9: STATE_ERROR,  # "Charging problem"
    10: STATE_PAUSED,  # "Paused"
    11: STATE_CLEANING,  # "Spot cleaning"
    12: STATE_ERROR,  # "Error"
    13: STATE_IDLE,  # "Shutting down"
    14: STATE_DOCKED,  # "Updating"
    15: STATE_RETURNING,  # "Docking"
    16: STATE_CLEANING,  # "Going to target"
    17: STATE_CLEANING,  # "Zoned cleaning"
    18: STATE_CLEANING,  # "Segment cleaning"
    22: STATE_DOCKED,  # "Emptying the bin" on s7+
    23: STATE_DOCKED,  # "Washing the mop" on s7maxV
    26: STATE_RETURNING,  # "Going to wash the mop" on s7maxV
    100: STATE_DOCKED,  # "Charging complete"
    101: STATE_ERROR,  # "Device offline"
}


ATTR_STATUS = "status"
ATTR_ERROR = "error"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Roborock sensor."""
    coordinator: RoborockDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    entities = []
    for device_id, device_info in coordinator.api.device_map.items():
        unique_id = slugify(device_id)
        entities.append(RoborockVacuum(unique_id, device_info, coordinator))
    async_add_entities(entities)


class RoborockVacuum(RoborockCoordinatedEntity, StateVacuumEntity, ABC):
    """General Representation of a Roborock vacuum."""

    def __init__(
        self,
        unique_id: str,
        device: RoborockDeviceInfo,
        coordinator: RoborockDataUpdateCoordinator,
    ) -> None:
        """Initialize a vacuum."""
        StateVacuumEntity.__init__(self)
        RoborockCoordinatedEntity.__init__(self, device, coordinator, unique_id)
        self.manual_seqnum = 0
        self._device = device
        self._coordinator = coordinator

    @property
    def supported_features(self) -> VacuumEntityFeature:
        """Flag vacuum cleaner features that are supported."""
        features = (
            VacuumEntityFeature.TURN_ON
            | VacuumEntityFeature.TURN_OFF
            | VacuumEntityFeature.PAUSE
            | VacuumEntityFeature.STOP
            | VacuumEntityFeature.RETURN_HOME
            | VacuumEntityFeature.FAN_SPEED
            | VacuumEntityFeature.BATTERY
            | VacuumEntityFeature.STATUS
            | VacuumEntityFeature.SEND_COMMAND
            | VacuumEntityFeature.LOCATE
            | VacuumEntityFeature.CLEAN_SPOT
            | VacuumEntityFeature.STATE
            | VacuumEntityFeature.START
            | VacuumEntityFeature.MAP
        )
        return features

    @property
    def icon(self) -> str:
        """Return the icon of the vacuum cleaner."""
        return "mdi:robot-vacuum"

    @property
    def state(self) -> str | None:
        """Return the status of the vacuum cleaner."""
        if not self._device_status:
            return None
        return STATE_CODE_TO_STATE.get(self._device_status.state)

    @property
    def status(self) -> str | None:
        """Return the status of the vacuum cleaner."""
        if not self._device_status:
            return None
        return self._device_status.status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the vacuum cleaner."""
        if not self._device_status:
            return {}
        data: dict[str, Any] = dict(self._device_status)

        if self.supported_features & VacuumEntityFeature.BATTERY:
            data[ATTR_BATTERY_LEVEL] = self.battery_level
            data[ATTR_BATTERY_ICON] = self.battery_icon

        if self.supported_features & VacuumEntityFeature.FAN_SPEED:
            data[ATTR_FAN_SPEED] = self.fan_speed

        data[ATTR_STATE] = self.state
        data[ATTR_STATUS] = self.status
        data[ATTR_ERROR] = self.error
        data.update(self.capability_attributes)

        return data

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the vacuum cleaner."""
        if not self._device_status:
            return None
        return self._device_status.battery

    @property
    def fan_speed(self) -> str | None:
        """Return the fan speed of the vacuum cleaner."""
        if not self._device_status:
            return None
        return self._device_status.fan_power

    @property
    def fan_speed_list(self) -> list[str]:
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return list(FAN_SPEED_CODES.values())

    @property
    def error(self) -> str | None:
        """Get the error str if an error code exists."""
        if not self._device_status:
            return None
        return self._device_status.error

    @property
    def capability_attributes(self) -> dict[str, list[str]]:
        """Return capability attributes."""
        capability_attributes = {}
        if self.supported_features & VacuumEntityFeature.FAN_SPEED:
            capability_attributes[ATTR_FAN_SPEED_LIST] = self.fan_speed_list
        return capability_attributes

    async def async_start(self) -> None:
        """Start the vacuum."""
        await self.send(RoborockCommand.APP_START)

    async def async_pause(self) -> None:
        """Pause the vacuum."""
        await self.send(RoborockCommand.APP_PAUSE)

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop the vacuum."""
        await self.send(RoborockCommand.APP_STOP)

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Send vacuum back to base."""
        await self.send(RoborockCommand.APP_CHARGE)

    async def async_clean_spot(self, **kwargs: Any) -> None:
        """Spot clean."""
        await self.send(RoborockCommand.APP_SPOT)

    async def async_locate(self, **kwargs: Any) -> None:
        """Locate vacuum."""
        await self.send(RoborockCommand.FIND_ME)

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set vacuum fan speed."""
        await self.send(
            RoborockCommand.SET_CUSTOM_MODE,
            [k for k, v in FAN_SPEED_CODES.items() if v == fan_speed],
        )
        await self.coordinator.async_request_refresh()

    async def async_start_pause(self):
        """Pause cleaning if running."""
        if self.state == STATE_CLEANING:
            await self.async_pause()
        else:
            # Start/resume cleaning.
            await self.async_start()

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a command to a vacuum cleaner."""
        return await self.send(command, params)
