"""Spook - Not your homie."""
from __future__ import annotations

from homeassistant.components import automation
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_component import DATA_INSTANCES, EntityComponent

from ....const import LOGGER
from ....repairs import AbstractSpookRepair


class SpookRepair(AbstractSpookRepair):
    """Spook repair tries to find unknown referenced devices in automations."""

    domain = automation.DOMAIN
    repair = "automation_unknown_device_references"
    inspect_events = {
        automation.EVENT_AUTOMATION_RELOADED,
        dr.EVENT_DEVICE_REGISTRY_UPDATED,
    }

    _entity_component: EntityComponent[automation.AutomationEntity]

    async def async_activate(self) -> None:
        """Handle the activating a repair."""
        self._entity_component = self.hass.data[DATA_INSTANCES][self.domain]
        await super().async_activate()

    async def async_inspect(self) -> None:
        """Trigger a inspection."""
        LOGGER.debug("Spook is inspecting: %s", self.repair)
        devices = {device.id for device in self.device_registry.devices.values()}
        for entity in self._entity_component.entities:
            if not isinstance(entity, automation.UnavailableAutomationEntity) and (
                unknown_devices := {
                    device
                    for device in entity.referenced_devices - devices
                    if isinstance(device, str) and device
                }
            ):
                self.async_create_issue(
                    issue_id=entity.entity_id,
                    translation_placeholders={
                        "devices": "\n".join(
                            f"- `{device}`" for device in unknown_devices
                        ),
                        "automation": entity.name,
                        "edit": f"/config/automation/edit/{entity.unique_id}",
                        "entity_id": entity.entity_id,
                    },
                )
                LOGGER.debug(
                    (
                        "Spook found unknown devices in %s "
                        "and created an issue for it; Areas: %s",
                    ),
                    entity.entity_id,
                    ", ".join(unknown_devices),
                )
            else:
                self.async_delete_issue(entity.entity_id)
