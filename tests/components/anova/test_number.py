"""Test Anova Numbers."""
from unittest.mock import AsyncMock

from anova_wifi import AnovaApi
import pytest

from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import async_init_integration

ENTITY_ID = "number.anova_precision_cooker"


async def test_set_value_temperature(
    hass: HomeAssistant,
    anova_api: AnovaApi,
    anova_precision_cooker: AsyncMock,
) -> None:
    """Test setting the temperature."""
    await async_init_integration(hass)
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: f"{ENTITY_ID}_target_temperature", ATTR_VALUE: 45.0},
        blocking=True,
    )
    assert anova_precision_cooker.set_target_temperature.call_args_list[0][0][0] == 45.0


async def test_set_value_temperature_failure(
    hass: HomeAssistant,
    anova_api: AnovaApi,
    anova_precision_cooker_setter_failure: AsyncMock,
) -> None:
    """Test setting the temperature with a failure."""
    await async_init_integration(hass)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: f"{ENTITY_ID}_target_temperature", ATTR_VALUE: 45.0},
            blocking=True,
        )


async def test_set_value_cook_time(
    hass: HomeAssistant,
    anova_api: AnovaApi,
    anova_precision_cooker: AsyncMock,
) -> None:
    """Test setting the cook time."""
    await async_init_integration(hass)
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: f"{ENTITY_ID}_cook_time", ATTR_VALUE: 900},
        blocking=True,
    )
    assert anova_precision_cooker.set_cook_time.call_args_list[0][0][0] == 900


async def test_set_value_cook_time_failure(
    hass: HomeAssistant,
    anova_api: AnovaApi,
    anova_precision_cooker_setter_failure: AsyncMock,
) -> None:
    """Test setting the cook time with a failure."""
    await async_init_integration(hass)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: f"{ENTITY_ID}_cook_time", ATTR_VALUE: 900},
            blocking=True,
        )
