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
    head: Optional[str] = None
    eyes: Optional[str] = None
    ears: Optional[str] = None
    neck: Optional[str] = None
    leftWrist: Optional[str] = None
    rightWrist: Optional[str] = None
    leftHand: Optional[str] = None
    rightHand: Optional[str] = None

class Character(BaseModel):
    userId: str = Field(..., min_length=1, description="length of characterId must be longer than 1")
    userName: str
    birthDate: str
    starBackground: str
    face: Face
    outfit: Outfit
    item: Item