from typing import Optional
from pydantic import BaseModel, Field, model_validator

class Face(BaseModel):
    skinColor: str
    hair: str
    eyes: str
    nose: str
    mouth: str
    mole: Optional[str] = ""

class Outfit(BaseModel):
    top: Optional[str] = ""
    bottom: Optional[str] = ""
    set: Optional[str] = ""
    shoes: str
    
    @model_validator(mode='after')
    def validate_top_set_exclusivity(self):
        if self.top and self.set:
            raise ValueError("Both 'top' and 'set' cannot be present at the same time")
        if not self.top and not self.set:
            raise ValueError("Either 'top' or 'set' must be present")
        return self

class Item(BaseModel):
    head: Optional[str] = ""
    eyes_item: Optional[str] = ""
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
    character: str
    profile: str
    face: Face
    outfit: Outfit
    item: Item