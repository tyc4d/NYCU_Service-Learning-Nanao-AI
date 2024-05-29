from fastapi import FastAPI, File, UploadFile, HTTPException 
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps
import os
import uuid
from vtoonify_api import process_image_with_vtoonify

app = FastAPI()

UPLOAD_FOLDER = "avatar_upload"
STYLED_FOLDER = "avatar_styled"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STYLED_FOLDER, exist_ok=True)

app.mount("/avatar_original", StaticFiles(directory=UPLOAD_FOLDER), name="avatar_original")
app.mount("/avatar_styled", StaticFiles(directory=STYLED_FOLDER), name="avatar_styled")

def is_valid_image(file: UploadFile):
    try:
        image = Image.open(file.file)
        image.verify()
        return True
    except Exception:
        return False

def process_image(file: UploadFile, user_id: str):
    file.file.seek(0)
    image = Image.open(file.file)
    image = ImageOps.pad(image, (512, 512), color='white')
    ext = file.filename.split('.')[-1]
    filename = f"original-{user_id}.{ext}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(path)
    return path

@app.post("/upload")
async def upload_image(file: UploadFile, user_id: str = None):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image type")

    if not is_valid_image(file):
        raise HTTPException(status_code=400, detail="Invalid image binary")

    if user_id == None:
        raise HTTPException(status_code=400, detail="Invalid User ID")
    try:
        original_path = process_image(file, user_id)
        ext = file.filename.split('.')[-1]

        styled_paths = []
        styles = [
            ("cartoon4-d", 0.5, 26),
            ("cartoon3-d", 0.75, 71),
            ("cartoon5-d", 0.5, 97)
        ]
        for i, (model_key, style_degree, style_id) in enumerate(styles, start=1):
            styled_filename = f"styled-ca{i}-{user_id}.{ext}"
            styled_path = os.path.join(STYLED_FOLDER, styled_filename)
            process_image_with_vtoonify(original_path, styled_path, model_key, style_degree, style_id)
            styled_paths.append(styled_path)

        return JSONResponse(content={"status": "ok", "styled_images": styled_paths})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
