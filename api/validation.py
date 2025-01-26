from pydantic import BaseModel, Field

class ItemData(BaseModel):
    name: str
    imgurl: str

class Face(BaseModel):
    skinColor: ItemData
    hair: ItemData
    expression: ItemData

class Outfit(BaseModel):
    top: ItemData
    bottom: ItemData
    shoes: ItemData

class Item(BaseModel):
    head: ItemData
    eyes: ItemData
    ears: ItemData
    neck: ItemData
    leftWrist: ItemData
    rightWrist: ItemData
    leftHand: ItemData
    rightHand: ItemData

class Character(BaseModel):
    characterId: str = Field(..., min_length=1, description="length of characterId must be longer than 1")
    characterName: str
    characterAge: int
    face: Face
    outfit: Outfit
    item: Item
    background: ItemData