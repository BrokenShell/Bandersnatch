""" Bandersnatch """
import numpy as np
from Fortuna import random_int, random_float, smart_clamp
from flask import Flask, render_template, request
import altair as alt
from joblib import load, dump

from app.db_ops import DataBase
from app.model import Model
from MonsterLab import Monster, Random

APP = Flask(__name__)
APP.db = DataBase()
APP.model = load("app/model.job")


@APP.route("/")
def home():
    monster = Monster()
    return render_template("home.html", monster=monster.to_dict())


def get_type(df, col):
    data_type = {
        np.float64: ":Q",
        np.int64: ":O",
    }
    if not df[col].empty:
        return data_type.get(type(df[col].iloc[0]), ":N")
    else:
        return ""


@APP.route("/view", methods=["GET", "POST"])
def view():
    raw_data = APP.db.get_df()
    if APP.db.get_count() == 0:
        return render_template(
            "view.html",
            total=0,
        )
    x_axis = request.values.get("x-axis") or "Health"
    y_axis = request.values.get("y-axis") or "Energy"
    target = request.values.get("target") or "Rarity"
    rarity = request.values.get("rarity") or "All"
    monsters = raw_data.drop(columns=['_id'])
    options = monsters.columns
    if rarity != "All":
        monsters = monsters[monsters['Rarity'] == rarity]
    total = monsters.shape[0]
    text_color = "#AAA"
    graph_color = "#333"
    graph_bg = "#252525"
    graph = alt.Chart(
        monsters,
        title=f"{rarity} Monsters",
    ).mark_circle(size=100).encode(
        x=alt.X(
            f"{x_axis}{get_type(monsters, x_axis)}",
            axis=alt.Axis(title=x_axis),
        ),
        y=alt.Y(
            f"{y_axis}{get_type(monsters, y_axis)}",
            axis=alt.Axis(title=y_axis),
        ),
        color=f"{target}{get_type(monsters, target)}",
        tooltip=alt.Tooltip(list(monsters.columns)),
    ).properties(
        width=400,
        height=480,
        background=graph_bg,
        padding=40,
    ).configure(
        legend={
            "titleColor": text_color,
            "labelColor": text_color,
            "padding": 10,
        },
        title={
            "color": text_color,
            "fontSize": 26,
            "offset": 30,
        },
        axis={
            "titlePadding": 20,
            "titleColor": text_color,
            "labelPadding": 5,
            "labelColor": text_color,
            "gridColor": graph_color,
            "tickColor": graph_color,
            "tickSize": 10,
        },
        view={
            "stroke": graph_color,
        },
    )
    return render_template(
        "view.html",
        rarity=rarity,
        rarity_options=["All", "Rank 1", "Rank 2", "Rank 3", "Rank 4", "Rank 5"],
        options=options,
        x_axis=x_axis,
        y_axis=y_axis,
        target_options=options,
        target=target,
        spec=graph.to_json(),
        total=total,
    )


@APP.route("/create", methods=["GET", "POST"])
def create():
    name = request.values.get("name")
    monster_type = request.values.get("type") or Random.random_type()
    level = int(request.values.get("level") or Random.random_level())
    rarity = request.values.get("rarity") or Random.random_rank()

    if not name:
        return render_template(
            "create.html",
            type_ops=Random.random_name.cat_keys,
            monster_type=monster_type,
            level_ops=list(range(1, 21)),
            level=level,
            rarity_ops=list(Random.dice.keys()),
            rarity=rarity,
        )

    if name.startswith("/"):
        _, com = name.split("/")
        if com == "reset":
            APP.db.reset_db()
        elif com.isnumeric():
            num = smart_clamp(1, int(com), 5000)
            APP.db.insert_many(Monster().to_dict() for _ in range(num))
        return render_template(
            "create.html",
            type_ops=Random.random_name.cat_keys,
            monster_type=monster_type,
            level_ops=list(range(1, 21)),
            level=level,
            rarity_ops=list(Random.dice.keys()),
            rarity=rarity,
        )

    monster = Monster(name, monster_type, level, rarity)
    APP.db.insert(monster.to_dict())
    return render_template(
        "create.html",
        type_ops=Random.random_name.cat_keys,
        monster_type=monster_type,
        level_ops=list(range(1, 21)),
        level=level,
        rarity_ops=list(Random.dice.keys()),
        rarity=rarity,
        monster=monster.to_dict(),
    )


@APP.route("/data", methods=["GET"])
def data():
    total = APP.db.get_count()
    if total > 0:
        df_table = APP.db.get_df().sort_values("Time Stamp", ascending=False)
        df_table = df_table.drop(columns=["_id"])
        df_html = df_table.to_html(index=False)
        return render_template(
            "data.html",
            total=total,
            df_table=df_html,
        )
    else:
        return render_template(
            "data.html",
            total=total,
        )


@APP.route("/predict", methods=["GET", "POST"])
def predict():

    def rand():
        return round(random_float(1, 200), 2)

    level = int(request.values.get("level") or random_int(1, 20))
    health = float(request.values.get("health") or rand())
    energy = float(request.values.get("energy") or rand())
    sanity = float(request.values.get("sanity") or rand())
    prediction, probability = APP.model([level, health, energy, sanity])
    train_score, test_score = APP.model.score()
    confidence = f"{100*probability*test_score:.2f}%"

    return render_template(
        "predict.html",
        level_ops=range(1, 21),
        level=level,
        health=health,
        energy=energy,
        sanity=sanity,
        prediction=prediction,
        confidence=confidence,
    )


@APP.route("/train", methods=["GET", "POST"])
def train():
    available = APP.db.get_count() - APP.model.total
    _, test_acc = APP.model.score()
    test_score = f"{100 * test_acc:.2f}%"

    return render_template(
        "train.html",
        test_score=test_score,
        available=available,
    )


@APP.route("/retrain", methods=["POST"])
def retrain():
    if APP.db.get_count() > 100:
        APP.model = Model()
        dump(APP.model, "app/model.job")
    return train()


if __name__ == "__main__":
    """ To run locally use the following command in the terminal:
    $ python3 -m app.main
    """
    APP.run()
