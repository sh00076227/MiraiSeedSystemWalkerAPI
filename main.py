from audioop import mul
import json
from fastapi import FastAPI,HTTPException
import uvicorn
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from util.util import Util
from api.api import API
from pydantic import BaseModel
app = FastAPI()

# CORSを回避するために追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#Python Run Uvicorn
if __name__ == '__main__':
    uvicorn.run("main:app", port=8000, reload=True)


##############################################
#ここにはルーティングの処理のみ記載してください。#
##############################################
@app.get("/")
def root():
    """
    @param  void
    @return message コメント
    """
    return {"message": "MiraiseedSystemWalkerAPI with FastAPI"}

#VMステータス返却
@app.get("/vm/status")
def getVmStatus():
    """
    @param  void
    @return 各面のステータス情報とロック状況を返却
    """
    return (API.getVmStatusMulti())

#VMステータス変更
@app.put("/vm/status/change")
def setVmStatus(VmChgParam=Body(...)):
    return API.setVmStatus(VmChgParam)