from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ecoharmonogram_client import EcoharmonogramClient
from ecoharmonogram_service import BadRequestError, EcoharmonogramScheduleService


class ScheduleRequest(BaseModel):
    town: str
    house_number: str
    street: str = ""
    district: str = ""
    additional_sides_matcher: str = ""
    community: str = ""
    app: str | None = None
    g1: str = ""
    g2: str = ""
    g3: str = ""
    g4: str = ""
    g5: str = ""


class TownLookupRequest(BaseModel):
    town: str = Field(default="")
    app: str | None = None
    community: str = ""


app = FastAPI(title="Ecoharmonogram API", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/towns")
def get_towns(payload: TownLookupRequest) -> dict:
    client = EcoharmonogramClient(app=payload.app)
    try:
        if payload.community:
            return client.fetch_towns_for_community(payload.community)
        return client.fetch_towns(payload.town)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/schedule")
def get_schedule(payload: ScheduleRequest) -> dict:
    try:
        service = EcoharmonogramScheduleService(**payload.model_dump())
        entries = service.fetch()
        entries_sorted = sorted(entries, key=lambda x: (x.date, x.waste_type))
        return {
            "count": len(entries_sorted),
            "entries": [
                {
                    "date": entry.date.isoformat(),
                    "type": entry.waste_type,
                }
                for entry in entries_sorted
            ],
        }
    except BadRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": exc.message,
                "suggestions": exc.suggestions,
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc