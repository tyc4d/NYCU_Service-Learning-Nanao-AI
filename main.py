from fastapi import FastAPI, File, UploadFile, HTTPException 
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps
from vtoonify_api import process_image_with_vtoonify
import os
import uuid
import uvicorn

app = FastAPI() # UVICORN main:app

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOAD_FOLDER = "avatar_upload" # 原始頭貼上傳目錄
STYLED_FOLDER = "avatar_styled" # 生成式AI產圖目錄

os.makedirs(UPLOAD_FOLDER, exist_ok=True) # 沒有的話會直接建立一個
os.makedirs(STYLED_FOLDER, exist_ok=True) # 沒有的話會直接建立一個

app.mount("/avatar_original", StaticFiles(directory=UPLOAD_FOLDER), name="avatar_original") # 將資料夾設為公開且為靜態資源
app.mount("/avatar_styled", StaticFiles(directory=STYLED_FOLDER), name="avatar_styled") # 將資料夾設為公開且為靜態資源

def is_valid_image(file: UploadFile): # 確認是正常的 image file (防止上船惡意執行檔案 etc...)
    try:
        image = Image.open(file.file)
        image.verify()
        return True
    except Exception:
        return False

def process_image(file: UploadFile, user_id: str): # 使用者上傳圖片會先做裁切壓縮
    file.file.seek(0)
    image = Image.open(file.file)
    image = ImageOps.pad(image, (512, 512), color='white')
    ext = file.filename.split('.')[-1]
    filename = f"original-{user_id}.{ext}" # 無論檔案名稱如何都重新命名給該 userid
    path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(path)
    return path

@app.post("/upload") # upload 路徑主程式
async def upload_image(file: UploadFile, user_id: str = None):
    if file.content_type not in ["image/jpeg", "image/png"]: # 確認 png or jpeg
        raise HTTPException(status_code=400, detail="Invalid image type") 

    if not is_valid_image(file): # 交由 python 認證檔案類型
        raise HTTPException(status_code=400, detail="Invalid image binary")

    if user_id == None: # 確認使用者是否有輸入 user id 
        raise HTTPException(status_code=400, detail="Empty User ID")

    if not user_id.isnumeric():
        raise HTTPException(status_code=400, detail="Invalid User ID")

    try: # 嘗試跑模型
        original_path = process_image(file, user_id)
        ext = file.filename.split('.')[-1]

        styled_paths = []
        styles = [ # model_key  style_degree  style_id
            ("cartoon4-d", 0.5, 26),
            ("cartoon3-d", 0.75, 71),
            ("cartoon5-d", 0.5, 97)
        ]
        for i, (model_key, style_degree, style_id) in enumerate(styles, start=1):
            styled_filename = f"styled-ca{i}-{user_id}.{ext}" # 重新命名
            styled_path = os.path.join(STYLED_FOLDER, styled_filename)
            process_image_with_vtoonify(original_path, styled_path, model_key, style_degree, style_id)
            styled_paths.append(styled_path)

        return JSONResponse(content={"status": "ok", "styled_images": styled_paths})
    except Exception as e: # 有問題直接丟例外
        if "NoneType" in str(e):
            raise HTTPException(status_code=400, detail="Please upload picture with face, Execption:"+str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
