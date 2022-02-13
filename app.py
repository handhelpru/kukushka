import sys
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
import mappings
import model_adapter
import random

origins = [
    "https://orakul.hand-help.ru",
    "https://angry-hypatia-500249.netlify.app/",
    "http://localhost:8081",
    "http://localhost:8082",
]


logger.remove()  # Removes default handler
logger.add(f"app.log",
           format="<white>{time:YYYY-M-D HH:mm:ss:SS}</white> "
           "<green>{module}:{function}:{line}</green> "
           "<level>{message}</level>")
logger.add(
    sys.stderr, colorize=True, backtrace=True, diagnose=True,
    format="<white>{time:YYYY-M-D HH:mm:ss:SS}</white> "
           "<green>{module}:{function}:{line}</green> "
           "<level>{message}</level>")


class RequestModel(BaseModel):
    sex: str
    region: str
    drug: str
    drug_amount: float
    """
    plea_guilty: int
    recidive: 
    imprisonment:
    """
    "отбывал ли ранее лишение свободы"
    # TODO: Add features, add validation
    pass


app = FastAPI()

fe = model_adapter.FeatureExtractor()
"""
sklearn_adapter = model_adapter.SklearnAdapter(
    model_fpath="model/model.pkl",
    label_encoder_path="model/type_label_encoder.pkl"
    )
xgboost_adapter = model_adapter.XgBoostAdapter()
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict")
def predict(request_data: RequestModel, request: Request):
    ip = request.client.host  # Change to 'X-forwarded-from" if using NGINX
    logger.info(f"Request from {ip}")

    try:
        now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        features = fe.extract_features(request_data=request_data)
        return {"response": model_adapter.XgBoostAdapter.predict(features)}

    except BaseException as e:
        logger.opt(exception=True).debug("Exception: ".format(e))
        return {"Exception: ": traceback.print_exc()}


@app.post("/test_predict")
def predict(request_data: RequestModel, request: Request):
    ip = request.client.host  # Change to 'X-forwarded-from" if using NGINX
    logger.info(f"Request from {ip}")

    try:
        now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        prediction = []
        for label in [0, 1, 2, 3]:
            d = {
                     "label": label,
                     "confidence": random.uniform(0, 1),
                     "scenario_id": mappings.get_punishment_name([label])
                 }
            prediction.append(d)
        return prediction

    except BaseException as e:
        logger.opt(exception=True).debug("Exception: ".format(e))
        return {"Exception: ": traceback.print_exc()}


@app.get("/metadata")
def metadata(request: Request):
    try:
        return mappings.mapping
    except BaseException as e:
        logger.opt(exception=True).debug("Exception: ".format(e))
        return {"Exception: ": traceback.print_exc()}
