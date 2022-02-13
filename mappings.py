from sklearn.preprocessing import LabelEncoder
import pickle

punishment_type_le = pickle.load(open('label_encoding/punishment_type_le.pkl', 'rb'))


def get_punishment_name(label):
    return punishment_type_le.inverse_transform(label)[0]

sex_mapping = {
    "Мужской": 0,
    "Женский": 1
}

mapping = {
    "sex": {
        "name": "Пол",
        "values": [
            {"value": "Мужчина", "id": 0},
            {"value": "Женщина", "id": 1}
        ]
    },
    "region": {
        "name": "Регион",
        "values": [
            {"value": "Санкт-Петербург", "id": 0},
            {"value": "Санкт-Петербур", "id": 1}
        ]
    },
    #"region": int,
    #"region": float,
    #"region":
    #"region":
    #"region":
}
