import datetime
from dataclasses import dataclass

from ecoharmonogram_client import EcoharmonogramClient


class BadRequestError(Exception):
    def __init__(self, message: str, suggestions: list[str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.suggestions = suggestions or []


@dataclass
class ScheduleEntry:
    date: datetime.date
    waste_type: str


class EcoharmonogramScheduleService:
    def __init__(
        self,
        town: str,
        house_number: str,
        district: str = "",
        street: str = "",
        additional_sides_matcher: str = "",
        community: str = "",
        app: str | None = None,
        g1: str = "",
        g2: str = "",
        g3: str = "",
        g4: str = "",
        g5: str = "",
    ) -> None:
        if not house_number:
            raise BadRequestError("house_number is required")

        self.town_input = town
        self.street_input = street
        self.house_number_input = house_number
        self.district_input = district
        self.additional_sides_matcher_input = additional_sides_matcher
        self.community_input = community
        self.groups = {"g1": g1, "g2": g2, "g3": g3, "g4": g4, "g5": g5}
        self.client = EcoharmonogramClient(app=app)

    def fetch(self) -> list[ScheduleEntry]:
        if self.community_input == "":
            town_data = self.client.fetch_towns(self.town_input)
        else:
            town_data = self.client.fetch_towns_for_community(self.community_input)

        towns = town_data.get("towns", [])
        matching_towns = [
            town for town in towns if self.town_input.lower() in town.get("name", "").lower()
        ]
        matching_towns_district = [
            town
            for town in matching_towns
            if self.district_input.lower() in town.get("district", "").lower()
        ]

        if len(matching_towns) == 0:
            suggestions = sorted({x.get("name", "") for x in towns if x.get("name")})
            raise BadRequestError(f"Town not found: {self.town_input}", suggestions)

        if len(matching_towns_district) == 0:
            suggestions = sorted(
                {x.get("district", "") for x in matching_towns if x.get("district")}
            )
            raise BadRequestError(f"District not found: {self.district_input}", suggestions)

        town = matching_towns_district[0]
        if len(matching_towns_district) > 1:
            exact = [
                t
                for t in matching_towns_district
                if self.town_input.lower() == t.get("name", "").lower()
                and self.district_input.lower() == t.get("district", "").lower()
            ]
            if exact:
                town = exact[0]
            else:
                suggestions = [
                    f"town: {x.get('name', '')}, district: {x.get('district', '')}"
                    for x in matching_towns_district
                ]
                raise BadRequestError("Multiple matching towns found without exact match", suggestions)

        schedule_periods_data = self.client.fetch_schedule_periods(town_id=town["id"])
        schedule_periods = schedule_periods_data.get("schedulePeriods", [])

        entries: list[ScheduleEntry] = []
        for period in schedule_periods:
            entries.extend(self._create_entries(period, town))
        return entries

    @staticmethod
    def _entry_exists(dmy: datetime.date, name: str, entries: list[ScheduleEntry]) -> bool:
        return any(dmy == e.date and name == e.waste_type for e in entries)

    def _get_streets_with_group(self, schedule_period: dict, town: dict) -> dict:
        group_id = "1"
        choosed_street_ids = ""
        counter = 0
        streets: dict = {"streets": [], "groups": {"items": [], "groupId": ""}}

        while group_id != "":
            counter += 1
            if counter > 6:
                raise BadRequestError("Infinite loop detected while fetching groups")

            streets = self.client.fetch_streets(
                schedule_period_id=schedule_period["id"],
                town_id=town["id"],
                street_name=self.street_input,
                house_number=self.house_number_input,
                group_id=group_id,
                choosed_street_ids=choosed_street_ids,
            )

            groups = streets.get("groups", {})
            group_id = groups.get("groupId", "")
            group_items = groups.get("items", [])

            if len(group_items) != 0 and group_id in self.groups:
                selected_group_name = self.groups[group_id]
                if selected_group_name == "":
                    suggestions = sorted({x.get("name", "") for x in group_items if x.get("name")})
                    raise BadRequestError(
                        f"{group_id} is required for this address",
                        suggestions,
                    )

                group_match = None
                for group in group_items:
                    if group.get("name", "").lower().casefold() == selected_group_name.lower().casefold():
                        group_match = group
                        choosed_street_ids = group.get("choosedStreetIds", "")

                if group_match is None:
                    suggestions = sorted({x.get("name", "") for x in group_items if x.get("name")})
                    raise BadRequestError(f"{group_id} not found: {selected_group_name}", suggestions)

        streets_list = streets.get("streets", [])
        if len(streets_list) == 1:
            return streets
        if len(streets_list) == 0:
            raise BadRequestError(f"Street not found: {self.street_input}")

        if self.additional_sides_matcher_input == "":
            suggestions = sorted({x.get("sides", "") for x in streets_list if x.get("sides")})
            raise BadRequestError("additional_sides_matcher is required", suggestions)

        to_return = [
            street
            for street in streets_list
            if street.get("sides", "") == ""
            or street.get("sides", "").lower().casefold()
            == self.additional_sides_matcher_input.lower().casefold()
        ]

        if len(to_return) == 0:
            suggestions = sorted({x.get("sides", "") for x in streets_list if x.get("sides")})
            raise BadRequestError(
                f"additional_sides_matcher not found: {self.additional_sides_matcher_input}",
                suggestions,
            )

        streets["streets"] = to_return
        return streets

    def _create_entries(self, schedule_period: dict, town: dict) -> list[ScheduleEntry]:
        streets = self._get_streets_with_group(schedule_period, town)

        entries: list[ScheduleEntry] = []
        for street in streets.get("streets", []):
            for street_id in street.get("id", "").split(","):
                schedules_response = self.client.fetch_schedules(
                    schedule_period_id=schedule_period["id"],
                    street_id=street_id,
                )

                if self.additional_sides_matcher_input.lower() not in schedules_response.get(
                    "street", {}
                ).get("sides", "").lower():
                    continue

                descriptions = {
                    sd["id"]: sd
                    for sd in schedules_response.get("scheduleDescription", [])
                    if sd.get("id")
                }

                for schedule in schedules_response.get("schedules", []):
                    description = descriptions.get(schedule.get("scheduleDescriptionId", ""), {})
                    name = description.get("name", "unknown")
                    days = schedule.get("days", "").split(";")
                    month = schedule.get("month")
                    year = schedule.get("year")

                    if not month or not year:
                        continue

                    for day in days:
                        if not day:
                            continue
                        dmy = datetime.date(int(year), int(month), int(day))
                        if not self._entry_exists(dmy, name, entries):
                            entries.append(ScheduleEntry(date=dmy, waste_type=name))

                if self.additional_sides_matcher_input == "":
                    return entries

        return entries