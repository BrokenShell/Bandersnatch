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
        target = df["Rarity"]
        features = df.drop(columns=["Rarity"])
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            features,
            target,
            test_size=0.20,
            stratify=target,
        )
        self.model = RandomForestClassifier(
            max_depth=12,
            bootstrap=False,
            n_jobs=-1,
            random_state=42,
            n_estimators=333,
        )
        self.model.fit(self.X_train, self.y_train)
        self.total = db.get_count()

    def __call__(self, feature_basis):
        prediction, *_ = self.model.predict([feature_basis])
        probability, *_ = self.model.predict_proba([feature_basis])
        return prediction, max(probability)

    @property
    def info(self):
        output = (
            f"Model: {str(self.model)}",
            f"Testing Score: {100*self.score():.5f}",
            f"Total Row Count: {self.total}",
            f"Training Row Count: {self.X_train.shape[0]}",
            f"Testing Row Count: {self.total - self.X_train.shape[0]}",
        )
        return "\n".join(output)

    def score(self):
        return self.model.score(self.X_test, self.y_test)


if __name__ == '__main__':
    model = Model()
    dump(model, "model.job")
    saved_model = load("model.job")
