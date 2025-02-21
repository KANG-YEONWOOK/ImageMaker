from typing import Optional
from pydantic import BaseModel, Field

class Face(BaseModel):
    skinColor: str
    hair: str
    expression: str

class Outfit(BaseModel):
    top: str
    bottom: str
    shoes: str

class Item(BaseModel):
    head: Optional[str] = ""
    eyes: Optional[str] = ""
    ears: Optional[str] = ""
    neck: Optional[str] = ""
    leftWrist: Optional[str] = ""
    rightWrist: Optional[str] = ""
    leftHand: Optional[str] = ""
    rightHand: Optional[str] = ""

class Character(BaseModel):
    userId: str = Field(..., min_length=1, description="length of characterId must be longer than 1")
    userName: str
    birthDate: str
    starBackground: str
    face: Face
    outfit: Outfit
    item: Item