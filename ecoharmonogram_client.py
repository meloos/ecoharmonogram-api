from random import randrange
from typing import Any

import requests

API_URL = "https://ecoharmonogram.pl/api/api.php"


class EcoharmonogramClient:
    def __init__(self, app: str | None = None) -> None:
        self._headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
        }
        self._app = app if app else None
        self._client_id = hex(randrange(0x1000000000000000, 0xFFFFFFFFFFFFFFFF))[2:]

    def _request(self, action: str, payload: dict[str, str | int]) -> dict[str, Any]:
        params = dict(payload)
        params["action"] = action
        if self._app:
            params["customApp"] = self._app
        params["funcVersion"] = 3
        params["appVersion"] = 107
        params["systemId"] = 1
        params["clientId"] = self._client_id
        params["lng"] = "pl"

        response = requests.post(API_URL, headers=self._headers, data=params, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8-sig"
        return response.json()

    def fetch_towns(self, town_name: str) -> dict[str, Any]:
        return self._request("getTowns", {"townName": town_name})

    def fetch_towns_for_community(self, community_id: str) -> dict[str, Any]:
        return self._request("getTownsForCommunity", {"communityId": community_id})

    def fetch_schedule_periods(self, town_id: str) -> dict[str, Any]:
        return self._request("getSchedulePeriods", {"townId": town_id})

    def fetch_streets(
        self,
        schedule_period_id: str,
        town_id: str,
        street_name: str,
        house_number: str,
        group_id: str = "1",
        choosed_street_ids: str = "",
    ) -> dict[str, Any]:
        payload: dict[str, str] = {
            "streetName": street_name,
            "number": house_number,
            "townId": town_id,
            "schedulePeriodId": schedule_period_id,
            "groupId": group_id,
            "choosedStreetIds": choosed_street_ids,
        }
        return self._request("getStreets", payload)

    def fetch_schedules(self, schedule_period_id: str, street_id: str) -> dict[str, Any]:
        return self._request(
            "getSchedules", {"streetId": street_id, "schedulePeriodId": schedule_period_id}
        )