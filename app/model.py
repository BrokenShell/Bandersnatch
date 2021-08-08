from joblib import dump, load
from sklearn.model_selection import train_test_split

from app.db_ops import DataBase
from sklearn.ensemble import RandomForestClassifier


class Model:

    def __init__(self):
        db = DataBase()
        df = db.get_df().drop(columns=[
            "_id", "Name", "Damage", "Type", "Time Stamp",
        ])
        target = df["Rank"]
        features = df.drop(columns=["Rank"])
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            features,
            target,
            test_size=0.20,
            stratify=target,
        )
        self.model = RandomForestClassifier()
        self.model.fit(self.X_train, self.y_train)

    def __call__(self, feature_basis):
        prediction, *_ = self.model.predict([feature_basis])
        probability, *_ = self.model.predict_proba([feature_basis])
        return prediction, max(probability)

    def score(self):
        train_score = self.model.score(self.X_train, self.y_train)
        test_score = self.model.score(self.X_test, self.y_test)
        return train_score - 0.0001, test_score


if __name__ == '__main__':
    model = Model()
    dump(model, "model.job")
    saved_model = load("model.job")
