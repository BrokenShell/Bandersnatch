import numpy as np
from flask import request
import altair as alt


def vis(raw_data):

    def get_type(df, col):
        data_type = {
            np.float64: ":Q",
            np.int64: ":O",
        }
        if not df[col].empty:
            return data_type.get(type(df[col].iloc[0]), ":N")
        else:
            return ""

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
    return filter_by, options, x_axis, y_axis, target, total, monsters, alt.Chart(
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
