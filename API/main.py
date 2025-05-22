# NOTE: API main file

import os
import sys
import dotenv

dotenv.load_dotenv()
sys.dont_write_bytecode = True
PATH = os.getenv('PROJECT_PATH')
sys.path.append(PATH)

from fastapi import FastAPI, HTTPException
from pipeline import run_cq_pipeline

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# API

class OutputParams(BaseModel):
    output_dir: Optional[str] = None
    output_file: Optional[str] = None
    save_file: bool = False

class SourceParams(BaseModel):
    start: Optional[str] = None
    end:   Optional[str] = None

class CQGramParams(BaseModel):
    tau1_list: List[float]
    tau2_list: List[float]

class Content(BaseModel):
    output_params: OutputParams
    source_params: SourceParams
    cqgram_params: CQGramParams
    tickers: Dict[str, str]

class RunRequest(BaseModel):
    source: str
    content: Content

app = FastAPI()

@app.post("/run")
def run(req: RunRequest):
    if req.source.lower() != "yahoo":
        raise HTTPException(
            status_code=400,
            detail=f"Bad source: {req.source} | supported sources: [Yahoo]",
        )
    return run_cq_pipeline(req.model_dump())
