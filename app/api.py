""" Bandersnatch """
from zipfile import ZipFile

import pandas as pd
from Fortuna import random_int, random_float
from MonsterLab import Monster, Random
from flask import Flask, render_template, request, send_file
import altair as alt
import numpy as np

from app.data import Data
from app.model import init_model


API = Flask(__name__)
API.db = Data()
API.model = init_model(API.db, force=True)


@API.route("/")
def home():
    return render_template("index.html")


@API.route("/view", methods=["GET", "POST"])
def view():

    def get_type(df, col):
        data_type = {
            np.float64: ":Q",
            np.int64: ":O",
        }
        if not df[col].empty:
            return data_type.get(type(df[col].iloc[0]), ":N")
        else:
            return ""

    alt.data_transformers.disable_max_rows()
    raw_data = API.db.get_df()
    if API.db.get_count({}) == 0:
        return render_template(
            "view.html",
            total=0,
        )
    x_axis = request.values.get("x-axis") or "Health"
    y_axis = request.values.get("y-axis") or "Energy"
    target = request.values.get("target") or "Rarity"
    filter_by = request.values.get("filter_by") or "All"
    monsters = raw_data.drop(columns=['_id'])
    options = monsters.columns
    if filter_by != "All":
        monsters = monsters[monsters['Rarity'] == filter_by]
    total = monsters.shape[0]
    text_color = "#AAA"
    graph_color = "#333"
    graph_bg = "#252525"
    graph = alt.Chart(
        monsters,
        title=f"{filter_by} Monsters",
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
    rarity_options = [
        "All",
        "Rank 0",
        "Rank 1",
        "Rank 2",
        "Rank 3",
        "Rank 4",
        "Rank 5",
    ]
    return render_template(
        "view.html",
        rarity=filter_by,
        rarity_options=rarity_options,
        options=options,
        x_axis=x_axis,
        y_axis=y_axis,
        target_options=options,
        target=target,
        spec=graph.to_json(),
        total=total,
        df_table=monsters.sort_index(ascending=False).to_html(),
    )


@API.route("/create", methods=["GET", "POST"])
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
            API.db.reset_db()
        elif com.isnumeric():
            API.db.insert_many(Monster().to_dict() for _ in range(int(com)))
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
    API.db.insert(monster.to_dict())
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


@API.route("/predict", methods=["GET", "POST"])
def predict():

    def rand():
        return round(random_float(1, 200), 2)

    level = int(request.values.get("level") or random_int(1, 20))
    health = float(request.values.get("health") or rand())
    energy = float(request.values.get("energy") or rand())
    sanity = float(request.values.get("sanity") or rand())
    prediction, probability = API.model([level, health, energy, sanity])
    test_score = API.model.score()
    confidence = f"{100*probability*test_score:.2f}%"

    graph_df = pd.DataFrame(
        {
            "Level": level_i,
            "Rank Predictions": API.model([level_i, health, energy, sanity])[0]
        } for level_i in range(1, 21)
    )
    text_color = "#AAA"
    graph_color = "#333"
    graph_bg = "#252525"
    graph = alt.Chart(
        graph_df,
        title=f"Rank Predictions by Level",
    ).mark_circle(size=100).encode(
        x=alt.X(
            "Rank Predictions",
            axis=alt.Axis(title="Ranks"),
        ),
        y=alt.Y(
            "Level",
            axis=alt.Axis(title="Levels"),
        ),
        color="Rank Predictions",
        tooltip=alt.Tooltip(list(graph_df.columns)),
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
        "predict.html",
        level_ops=range(1, 21),
        level=level,
        health=health,
        energy=energy,
        sanity=sanity,
        prediction=prediction,
        confidence=confidence,
        graph_json=graph.to_json(),
    )


@API.route("/train", methods=["GET", "POST"])
def train():
    name = API.model.name
    time_stamp = API.model.time_stamp
    test_score = f"{100 * API.model.score():.3f}%"
    total = API.model.total_db
    available = API.db.get_count({}) - total

    return render_template(
        "train.html",
        name=name,
        time_stamp=time_stamp,
        test_score=test_score,
        total=total,
        available=available,
    )


@API.route("/retrain", methods=["GET", "POST"])
def retrain():
    if all(x > 2 for x in API.db.get_df()["Rarity"].value_counts()):
        API.model = init_model(API.db, force=True)
    else:
        print("Training Error! Get more data.")
    return train()


@API.route("/download", methods=["GET"])
def download():
    with ZipFile("app/saved_model/saved_model.zip", "w") as archive:
        archive.write("app/saved_model/notes.txt", "saved_model/notes.txt")
        archive.write("app/saved_model/data.csv", "saved_model/data.csv")
        archive.write("app/saved_model/model.job", "saved_model/model.job")
    return send_file("saved_model/saved_model.zip", as_attachment=True)


if __name__ == "__main__":
    """ To run locally use the following command in the terminal:
    $ python -m app.main
    """
    API.run()
