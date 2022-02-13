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
import regex_patterns


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
    sex: bool
    region: str
    drug: str
    drug_amount: float
    conviction: bool
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
        label = random.randint(0, 3)
        punishment_text = mappings.get_punishment_name([label])
        if punishment_text == "Уголовные или исправительные работы":
            punishment_text = "Обязательные/исправительные работы"

        drug_name = request_data.drug
        for k,v in regex_patterns.drug_clean_dict.items():
            if v == drug_name:
                regex_drug_name = k
                break

        def get_size_id(sizes, drug_amount):
            for s in sizes:
                if drug_amount < s:
                    return sizes.index(s)

        sizes = regex_patterns.drugs_sizes.get(regex_drug_name)
        size = get_size_id(sizes, request_data.drug_amount)
        if size == 3:
            scenario_id = 3
        if size == 3:
            scenario_id = 4
        if size == 1:
            scenario_id = 5
        if not request_data.conviction and size == 2:
            scenario_id = 1
        if request_data.conviction and size == 2:
            scenario_id = 2


        prediction = {
            "label": label,
            "confidence": random.uniform(0.4, 1),
            "punishment_text": punishment_text,
            'scenario_id': scenario_id
                 }
        return prediction

    except BaseException as e:
        logger.opt(exception=True).debug("Exception: ".format(e))
        return {"Exception: ": traceback.print_exc()}


@app.post("/test_predict")
def test_predict(request_data: RequestModel, request: Request):
    ip = request.client.host  # Change to 'X-forwarded-from" if using NGINX
    logger.info(f"Request from {ip}")

    try:
        now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        label = random.randint(0, 3)
        punishment_text = mappings.get_punishment_name([label])
        if punishment_text == "Уголовные или исправительные работы":
            punishment_text = "Обязательные/исправительные работы"

        prediction = {
            "label": label,
            "confidence": random.uniform(0.4, 1),
            "punishment_text": punishment_text,
            'scenario_id': None
                 }
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
