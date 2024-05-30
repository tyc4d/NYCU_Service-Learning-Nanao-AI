# NYCU_Service-Learning-Nanao-AI

## 簡介

這是陽明交通大學112學年度服務學習的專案，南澳資料庫系統，主要功能其實是協助病患可以跟根據時間填寫身體各個部位的疼痛指數。
而其中這個專案專門在做Q版頭貼的部分，利用生成式 AI Pre-traian model 在 CPU only 伺服器上執行將用戶上傳之頭貼卡通化

## 安裝

```bash
pip install -r requirments.txt
```

若有 dlib 無法編譯的問題請參考以下指令預先做編譯

```bash
git clone https://github.com/davisking/dlib.git
cd dlib
mkdir build; cd build; cmake ..; cmake --build .
cd ..
python3 setup.py install
```

## 執行

單執行緒
```bash
python main.py
```

多 worker 執行方法
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

## 引用

本專案之模型以及模組是基於 [Vtoonify](https://github.com/williamyang1991/VToonify) by Prof. Chen Change Loy