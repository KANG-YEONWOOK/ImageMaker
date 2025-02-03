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
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 Origin
    allow_credentials=True,  # 인증 정보 포함 허용 여부 (쿠키 등)
    allow_methods=["*"],  # 허용할 HTTP 메서드 (GET, POST 등)
    allow_headers=["*"],  # 허용할 HTTP 헤더
)

def get_image(url):
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
        f"{PINATA_ENDPOINT}{image_data["face"]["skinColor"]}.png",
        f"{PINATA_ENDPOINT}{image_data["face"]["hair"]}.png",
        f"{PINATA_ENDPOINT}{image_data["face"]["expression"]}.png",
        f"{PINATA_ENDPOINT}{image_data["outfit"]["top"]}.png",
        f"{PINATA_ENDPOINT}{image_data["outfit"]["bottom"]}.png",
        f"{PINATA_ENDPOINT}{image_data["outfit"]["shoes"]}.png",
        f"{PINATA_ENDPOINT}{image_data["item"]["head"]}.png",
        f"{PINATA_ENDPOINT}{image_data["item"]["eyes"]}.png",
        f"{PINATA_ENDPOINT}{image_data["item"]["ears"]}.png",
        f"{PINATA_ENDPOINT}{image_data["item"]["neck"]}.png",
        f"{PINATA_ENDPOINT}{image_data["item"]["leftWrist"]}.png",
        f"{PINATA_ENDPOINT}{image_data["item"]["rightWrist"]}.png",
        f"{PINATA_ENDPOINT}{image_data["item"]["leftHand"]}.png",
        f"{PINATA_ENDPOINT}{image_data["item"]["rightHand"]}.png",
    ]
    
    layered_img = get_image(layers[0])

    for layer_url in layers[1:]:
        if(layer_url==""):
            pass
        else:
            img = get_image(layer_url)
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

    return request_folder
    

def upload_to_ipfs(file_path):
    with open(file_path, "rb") as file:
        response = requests.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS", headers=HEADER, files={"file": file}
        )
    if response.status_code == 200:
        return response.json()["IpfsHash"]
    else:
        raise HTTPException(status_code=500, detail="IPFS upload failed")


def checkExistence(user_id): # 이미지가 존재하면 삭제하는 로직
    response = requests.get(
            "https://api.pinata.cloud/data/pinList?status=pinned", headers=HEADER
        )
    file_list = response.json()["rows"]
    for file_info in file_list:
        if(file_info["metadata"]["name"] == f"{user_id}"):
            delete_response = requests.delete(f"https://api.pinata.cloud/pinning/unpin/{file_info["ipfs_pin_hash"]}", headers=HEADER)
            return delete_response.text
    return "OK"


@app.post('/profile')
async def upload_profile(data:Character):
    try:
        user_id = data.userId
        check = checkExistence(user_id)
        if(check != "OK"):
            return {
                "state": "Fail",
                "characterId": "",
                "img_url": ""
            }
        request_folder = process_image(data.model_dump(), user_id)
        
        ipfs_hash = upload_to_ipfs(request_folder)
        ipfs_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
        
        shutil.rmtree(request_folder)

        return {
            "state": "Success",
            "userId": user_id,
            "img_url": ipfs_url
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
