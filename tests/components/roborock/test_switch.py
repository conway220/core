"""Test Roborock Switch platform."""
from unittest.mock import patch

import pytest
from roborock.exceptions import RoborockException

from homeassistant.components.switch import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from tests.common import MockConfigEntry


@pytest.mark.parametrize(
    ("entity_id"),
    [
        ("switch.roborock_s7_maxv_child_lock"),
        ("switch.roborock_s7_maxv_status_indicator_light"),
        ("switch.roborock_s7_maxv_do_not_disturb"),
    ],
)
async def test_update_success(
    hass: HomeAssistant,
    bypass_api_fixture,
    setup_entry: MockConfigEntry,
    entity_id: str,
) -> None:
    """Test turning switch entities on and off."""
    # Ensure that the entity exist, as these test can pass even if there is no entity.
    assert hass.states.get(entity_id) is not None
    with patch(
        "homeassistant.components.roborock.coordinator.RoborockLocalClient._send_command"
    ) as mock_send_message:
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_ON,
            service_data=None,
            blocking=True,
            target={"entity_id": entity_id},
        )
    assert mock_send_message.assert_called_once
    with patch(
        "homeassistant.components.roborock.coordinator.RoborockLocalClient.send_message"
    ) as mock_send_message:
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_OFF,
            service_data=None,
            blocking=True,
            target={"entity_id": entity_id},
        )
    assert mock_send_message.assert_called_once


async def test_update_failure(
    hass: HomeAssistant,
    bypass_api_fixture,
    setup_entry: MockConfigEntry,
) -> None:
    """Check that when the api fails to update, we raise a error."""
    assert hass.states.get("switch.roborock_s7_maxv_child_lock") is not None
    with patch(
        "homeassistant.components.roborock.coordinator.RoborockLocalClient.send_message",
        side_effect=RoborockException(),
    ), pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_ON,
            service_data=None,
            blocking=True,
            target={"entity_id": "switch.roborock_s7_maxv_child_lock"},
        )
    with patch(
        "homeassistant.components.roborock.coordinator.RoborockLocalClient.send_message",
        side_effect=RoborockException(),
    ), pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_OFF,
            service_data=None,
            blocking=True,
            target={"entity_id": "switch.roborock_s7_maxv_child_lock"},
        )
