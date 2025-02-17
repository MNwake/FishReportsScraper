from typing import List, Optional, Dict
from typing import Tuple

from pydantic import BaseModel


class Species(BaseModel):
    code: str
    common_name: str
    scientific_name: str
    game_fish: bool
    species_group: str


class FishCount(BaseModel):
    length: Optional[int] = None
    quantity: Optional[int] = None


class LengthData(BaseModel):
    species: Optional[Species] = None  # Replace string with Species model
    fishCount: Optional[List[FishCount]] = None
    minimum_length: Optional[int] = None
    maximum_length: Optional[int] = None


# Fish catch summaries
class FishCatchSummary(BaseModel):
    CPUE: Optional[str] = None
    quartileCount: Optional[str] = None
    totalWeight: Optional[float] = None
    gearCount: Optional[float] = None
    quartileWeight: Optional[str] = None
    species: Optional[str] = None
    gear: Optional[str] = None
    averageWeight: Optional[str] = None
    totalCatch: Optional[int] = None


# Survey data
class Survey(BaseModel):
    surveyID: str
    fishCatchSummaries: Optional[List[FishCatchSummary]] = []
    narrative: Optional[str] = None
    headerInfo: List[Optional[str]] = []
    surveyType: str
    surveySubType: str
    surveyDate: str
    lengths: Optional[Dict[str, LengthData]] = {}


# Access data
class Accesses(BaseModel):
    location: str
    ownerTypeID: Optional[str] = None
    accessTypeID: Optional[str] = None
    publicUseAuthCode: Optional[str] = None
    lakeAccessComments: Optional[str] = None


# Result data
class Result(BaseModel):
    lakeName: str
    countyName: str
    sampledPlants: List[str] = []
    shoreLengthMiles: Optional[float] = None
    DOWNumber: int
    waterClarity: List[Tuple[str, str]] = []
    averageWaterClarity: Optional[str] = None
    littoralAcres: Optional[float] = None
    areaAcres: Optional[float] = None
    meanDepthFeet: Optional[float] = None
    maxDepthFeet: Optional[float] = None
    officeCode: Optional[str] = None
    accesses: Optional[List[Accesses]] = []
    surveys: Optional[List[Survey]] = []


# Top-level schema
class FishData(BaseModel):
    timestamp: Optional[int] = None  # Default to None if missing
    result: Optional[Result] = None
    status: Optional[str] = None
    message: Optional[str] = None

