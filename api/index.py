from fastapi import FastAPI, HTTPException
from PIL import Image, ImageDraw
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from api.validation import Character
import shutil
import os
import requests

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_ENDPOINT = os.environ.get("PINATA_ENDPOINT")
HEADER = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_API_SECRET,
    }

if not (PINATA_API_KEY and PINATA_API_SECRET):
    raise RuntimeError("Missing PINATA API credentials or endpoint in environment variables")

origins = [
    "http://pleiades-front-deploy.s3-website.ap-northeast-2.amazonaws.com",
    "https://your-pleiades.com"
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 Origin
    allow_credentials=True,  # 인증 정보 포함 허용 여부 (쿠키 등)
    allow_methods=["*"],  # 허용할 HTTP 메서드 (GET, POST 등)
    allow_headers=["*"],  # 허용할 HTTP 헤더
)

def get_image(fileName):
    url = f"{PINATA_ENDPOINT}/{fileName}.png"
    if(url == ""): return None
    response = requests.get(url)
    if(response.status_code == 200):
        return Image.open(BytesIO(response.content)).convert("RGBA")
    else:
        return False

def process_image(image_data, user_id):
    temp_folder = "/tmp"
    request_folder = os.path.join(temp_folder, user_id)
    os.makedirs(request_folder, exist_ok=True)
    profile_output_path = os.path.join(request_folder, f"{user_id}Profile.png")
    character_output_path = os.path.join(request_folder, f"{user_id}.png")

    layers = [
        image_data["face"]["skinColor"],
        image_data["face"]["hair"],
        image_data["face"]["expression"],
        image_data["outfit"]["bottom"],
        image_data["outfit"]["top"],
        image_data["outfit"]["shoes"],
        image_data["item"]["head"],
        image_data["item"]["eyes"],
        image_data["item"]["ears"],
        image_data["item"]["neck"],
        image_data["item"]["leftWrist"],
        image_data["item"]["rightWrist"],
        image_data["item"]["leftHand"],
        image_data["item"]["rightHand"],
    ]
    
    layered_img = get_image(layers[0])

    for layer_url in layers[1:]:
        if(layer_url=="" or layer_url==None):
            pass
        else:
            img = get_image(layer_url)
            width, height = layered_img.size
            img = img.resize((width,height))
            layered_img = Image.alpha_composite(layered_img, img)
    
    layered_img.save(character_output_path, format="PNG")
    
    width, height = layered_img.size
    background_color = (187, 196, 225, 255)
    background_img = Image.new("RGBA", (width, height), background_color)
    layered_img = Image.alpha_composite(background_img, layered_img)
    layered_img = layered_img.crop((80,90,width-80,(3*height)//5 - 10))
    layered_img = layered_img.resize((120,120))
    mask = Image.new("L", (120, 120), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0,0,120,120), fill=255)
    layered_img = Image.composite(layered_img, Image.new("RGBA", (120, 120), (0, 0, 0, 0)), mask)

    layered_img.save(profile_output_path, format="PNG")

    return profile_output_path, character_output_path, request_folder
    

def upload_to_ipfs(file_path):
    with open(file_path, "rb") as file:
        response = requests.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS", headers=HEADER, files={"file": file}
        )
    if response.status_code == 200:
        print(response.json()["IpfsHash"])
        return response.json()["IpfsHash"]
    else:
        raise HTTPException(status_code=500, detail="IPFS upload failed")


def checkExistence(fileName): # 이미지가 존재하면 삭제하는 로직
    response = requests.get(
            "https://api.pinata.cloud/data/pinList?status=pinned", headers=HEADER
        )
    file_list = response.json()["rows"]
    for file_info in file_list:
        if(file_info["metadata"]["name"] == f"{fileName}.png"):
            delete_response = requests.delete(f"https://api.pinata.cloud/pinning/unpin/{file_info["ipfs_pin_hash"]}", headers=HEADER)
            return delete_response.text
    return "OK"


@app.post('/profile')
async def upload_profile(data:Character):
    try:
        user_id = data.userId
        fileNames = [user_id, f"{user_id}Profile"]
        for fileName in fileNames:
            check = checkExistence(fileName)
            if(check != "OK"):
                raise HTTPException(status_code=500, detail="Failure occured while delete image")
        profile_output_path, character_output_path, request_folder = process_image(data.model_dump(), user_id)
        
        profile_ipfs_hash = upload_to_ipfs(profile_output_path)
        character_ipfs_hash = upload_to_ipfs(character_output_path)
        profile_ipfs_url = f"https://gateway.pinata.cloud/ipfs/{profile_ipfs_hash}"
        character_ipfs_url = f"https://gateway.pinata.cloud/ipfs/{character_ipfs_hash}"
        
        shutil.rmtree(request_folder)

        return {
            "userId": user_id,
            "profile": profile_ipfs_url,
            "character": character_ipfs_url
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
