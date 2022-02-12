import sys
import numpy as np
import random
from loguru import logger
from joblib import load


class FeatureExtractor:
    def __init__(self):
        pass

    @staticmethod
    def extract_features(request_data):
        # feature_dict['filename'] = fpath
        # feature_dict['duration'] = len(wf.waveform) / wf.sample_rate
        logger.info(f"request_data: {request_data}")
        features = np.array(list(request_data.values())).reshape(1, -1)
        return features


class SklearnAdapter:
    models_fpath = ''

    def __init__(self, **kwargs):
        logger.info(f"Loading SklearnAdapter with kwargs: {kwargs}")
        self.model = None

    @staticmethod
    def load_model(model_fpath: str):
        return load(model_fpath)

    @staticmethod
    def test_predict(features):
        logger.debug(f"Features size: {type(features)}, size: {sys.getsizeof(features)}")
        prediction = {
            "prediction": random.sample([0, 1], 1)[0],
            "confidence": random.uniform(0, 1)
        }
        return prediction

    @staticmethod
    def predict(features):
        model = SklearnAdapter.load_model(SklearnAdapter.model_fpath)
        logger.debug(f"Features size: {type(features)}, size: {sys.getsizeof(features)}")
        prediction = {
            "prediction": model.predict(features),
            "confidence": model.predict_proba(features)
        }
        return prediction


class XgBoostAdapter:
    model_fpath = ''
    label_map = {
        0: "",
        1: ""
    }

    def __init__(self, **kwargs):
        logger.info(f"Loading SklearnAdapter with kwargs: {kwargs}")
        self.model = self.load_model(self.model_fpath)

    @staticmethod
    def load_model(model_fpath: str):
        return load(model_fpath)

    @staticmethod
    def test_predict(features):
        logger.debug(f"Features size: {type(features)}, size: {sys.getsizeof(features)}")
        prediction = {
            "prediction": random.sample([0, 1], 1)[0],
            "confidence": random.uniform(0, 1)
        }
        return prediction

    def predict_single(self, features):
        logger.debug(f"Features size: {type(features)}, size: {sys.getsizeof(features)}")
        prediction = self.model.predict(features)[0]
        prediction_proba = self.model.predict_proba(features)[0]
        logger.debug(f"Prediction: {prediction}")
        logger.debug(f"prediction_proba: {prediction_proba}")
        prediction = {
            "prediction": self.label_map.get(prediction),
            "confidence": str(max(prediction_proba)),
        }
        return prediction

    def predict_multi(self, features):
        logger.debug(f"Features size: {type(features)}, size: {sys.getsizeof(features)}")
        prediction = self.model.predict(features)
        prediction_proba = self.model.predict_proba(features)
        logger.debug(f"Prediction: {prediction}")
        logger.debug(f"prediction_proba: {prediction_proba}")
        result = []
        for p, pp in zip(prediction, prediction_proba):
            prediction = {
                "prediction": self.label_map.get(p),
                "confidence": str(max(pp)),
            }
            result.append(prediction)

        return result


if __name__ == "__main__":
    test_features = ""
    features = FeatureExtractor().extract_features(test_features)
    """
    sklearn_adapter = SklearnAdapter(
        model_fpath="model/model.pkl",
        label_encoder_path="model/type_label_encoder.pkl"
    )
    logger.debug(sklearn_adapter.test_predict(features=features))
    """