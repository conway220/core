"""Support for Anova Numbers."""
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from anova_wifi import AnovaException, APCUpdate

from homeassistant import config_entries
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .coordinator import AnovaCoordinator
from .entity import AnovaDescriptionEntity
from .models import AnovaData


@dataclass
class AnovaNumberEntityDescriptionMixin:
    """Describes the extra Anova number description values."""

    set_value_fn: Callable[[tuple[AnovaCoordinator, float]], Coroutine[Any, Any, None]]
    get_value_fn: Callable[[APCUpdate], float | int]


@dataclass
class AnovaNumberEntityDescription(
    NumberEntityDescription, AnovaNumberEntityDescriptionMixin
):
    """Describes a Anova number entity."""


NUMBER_DESCRIPTIONS = [
    AnovaNumberEntityDescription(
        key="target_temperature",
        translation_key="target_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=0.0,
        native_max_value=63.33,
        set_value_fn=lambda data: data[0].anova_device.set_target_temperature(data[1]),
        get_value_fn=lambda data: data.sensor.target_temperature,
    ),
    AnovaNumberEntityDescription(
        key="cook_time",
        translation_key="cook_time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=0,
        native_max_value=356400,
        set_value_fn=lambda data: data[0].anova_device.set_cook_time(int(data[1])),
        get_value_fn=lambda data: data.sensor.cook_time,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Anova device."""
    anova_data: AnovaData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AnovaNumber(coordinator, description)
        for coordinator in anova_data.coordinators
        for description in NUMBER_DESCRIPTIONS
    )


class AnovaNumber(AnovaDescriptionEntity, NumberEntity):
    """Describes a Number."""

    entity_description: AnovaNumberEntityDescription

    async def async_set_native_value(self, value: float) -> None:
        """Set the Number Entity's value."""
        try:
            await self.entity_description.set_value_fn((self.coordinator, value))
        except AnovaException as err:
            raise HomeAssistantError(
                f"Could not set {self.entity_description.key}"
            ) from err
        await self.coordinator.async_request_refresh()

    @property
    def native_value(self) -> float | None:
        """Gets the current value of the number entity."""
        return self.entity_description.get_value_fn(self.coordinator.data)
