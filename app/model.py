from datetime import datetime

import pytz
from joblib import dump, load
from sklearn.model_selection import train_test_split
from os import path

from app.data import Data
from sklearn.ensemble import RandomForestClassifier


class Model:

    def __init__(self, db: Data):
        df = db.get_df().drop(columns=[
            "_id", "Name", "Damage", "Type", "Time Stamp",
        ])
        target = df["Rarity"]
        features = df.drop(columns=["Rarity"])
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            features,
            target,
            test_size=0.20,
            stratify=target,
            random_state=42,
        )
        self.total_db = db.get_count({})
        self.total_trained = self.y_train.shape[0]
        self.total_tested = self.y_test.shape[0]
        self.model = RandomForestClassifier(
            class_weight={
                'Rank 0': 0.306059,
                'Rank 1': 0.249341,
                'Rank 2': 0.194335,
                'Rank 3': 0.138978,
                'Rank 4': 0.083304,
                'Rank 5': 0.027983,
            },
            n_jobs=-1,
            random_state=42,
        )
        self.name = str(self.model).split('(')[0]
        lambda_time = pytz.timezone('US/Pacific')
        start_time = datetime.now(lambda_time)
        self.model.fit(self.X_train, self.y_train)
        stop_time = datetime.now(lambda_time)
        self.duration = stop_time - start_time
        self.time_stamp = stop_time.strftime('%Y-%m-%d %H:%M:%S')

    def __call__(self, feature_basis):
        prediction, *_ = self.model.predict([feature_basis])
        probability, *_ = self.model.predict_proba([feature_basis])
        return prediction, max(probability)

    @property
    def info(self):
        output = (
            f"Model: {self.model}",
            f"Time Stamp: {self.time_stamp}",
            f"Testing Score: {100 * self.score():.3f}%",
            f"Total Row Count: {self.total_db}",
            f"Training Row Count: {self.total_trained}",
            f"Testing Row Count: {self.total_tested}",
            f"Time to Train: {self.duration}",
        )
        return "\n".join(output)

    def score(self):
        return self.model.score(self.X_test, self.y_test)


def init_model(db: Data, force=False):
    if not force and path.exists("app/saved_model/model.job"):
        model = load("app/saved_model/model.job")
    else:
        model = Model(db)
        dump(model, "app/saved_model/model.job")
        db.get_df().to_csv("app/saved_model/data.csv", index=False)
        with open("app/saved_model/notes.txt", "w") as file:
            file.write(model.info)
    return model
