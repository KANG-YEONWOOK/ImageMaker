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
    head: str
    eyes: str
    ears: str
    neck: str
    leftWrist: str
    rightWrist: str
    leftHand: str
    rightHand: str

class Character(BaseModel):
    userId: str = Field(..., min_length=1, description="length of characterId must be longer than 1")
    userName: str
    birthDate: str
    backgroundName: str
    face: Face
    outfit: Outfit
    item: Item