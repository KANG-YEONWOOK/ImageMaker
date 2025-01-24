from fastapi import FastAPI, HTTPException
from PIL import Image, ImageDraw
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import requests

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_ENDPOINT = os.environ.get("PINATA_ENDPOINT")

if not (PINATA_API_KEY and PINATA_API_SECRET and PINATA_ENDPOINT):
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

PROCESSED_FOLDER = "/tmp"

def get_image(url):
    if(url == ""): return None
    response = requests.get(url)
    if(response.status_code == 200):
        return Image.open(BytesIO(response.content)).convert("RGBA")
    else:
        return False

def process_image(image_data, character_id):
    request_folder = os.path.join(PROCESSED_FOLDER, character_id)
    os.makedirs(request_folder, exist_ok=True)
    output_path = os.path.join(request_folder, "final_image.png")

    layers = [
        image_data["face"]["skinColor"]["imgurl"],
        image_data["face"]["hair"]["imgurl"],
        image_data["face"]["expression"]["imgurl"],
        image_data["outfit"]["top"]["imgurl"],
        image_data["outfit"]["bottom"]["imgurl"],
        image_data["outfit"]["shoes"]["imgurl"],
        image_data["item"]["head"]["imgurl"],
        image_data["item"]["eyes"]["imgurl"],
        image_data["item"]["ears"]["imgurl"],
        image_data["item"]["neck"]["imgurl"],
        image_data["item"]["leftWrist"]["imgurl"],
        image_data["item"]["rightWrist"]["imgurl"],
        image_data["item"]["leftHand"]["imgurl"],
        image_data["item"]["rightHand"]["imgurl"],
    ]
    
    layered_img = get_image(layers[0])

    for layer_url in layers[1:]:
        if(layer_url==""):
            pass
        else:
            img = get_image(layer_url)
            layered_img = Image.alpha_composite(layered_img, img)
    
    width, height = layered_img.size
    background_color = (187, 196, 225, 255)
    background_img = Image.new("RGBA", (width, height), background_color)
    layered_img = Image.alpha_composite(background_img, layered_img)
    layered_img = layered_img.crop((80,90,width-80,(3*height)//5 - 10))
    layered_img = layered_img.resize((70,70))
    mask = Image.new("L", (70, 70), 0) 
    draw = ImageDraw.Draw(mask)
    center_x, center_y = 35,35
    radius = 35  # 원의 반지름
    draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), fill=255)
    layered_img = Image.composite(layered_img, Image.new("RGBA", (70, 70), (0, 0, 0, 0)), mask)

    layered_img.save(output_path, format="PNG")

    return output_path, request_folder
    

def upload_to_ipfs(file_path):
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_API_SECRET,
    }
    with open(file_path, "rb") as file:
        response = requests.post(
            PINATA_ENDPOINT, headers=headers, files={"file": file}
        )
    if response.status_code == 200:
        return response.json()["IpfsHash"]
    else:
        raise HTTPException(status_code=500, detail="IPFS upload failed")
    

@app.post('/profile')
async def upload_profile(data:dict):
    try:
        character_id = data.get("characterId")
        
        processed_path, request_folder = process_image(data, character_id)
        
        ipfs_hash = upload_to_ipfs(processed_path)
        ipfs_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
        
        shutil.rmtree(request_folder)

        return {
            "characterId": character_id,
            "img_url": ipfs_url
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

