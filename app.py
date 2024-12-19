import os
import json
import numpy as np
import pickle
import pandas as pd
import plotly
import plotly.subplots
import plotly.graph_objects as go
from flask import Flask, abort, redirect, url_for, render_template, send_file
from flask_restful import Api
from dash import Dash, html, dash_table, dcc, Output, Input, State
import dash_bootstrap_components as dbc
from data import complete_dataframe as GLOBAL_DF
from pregpk.front_end.front_end import read_utils, page_layouts, data_utils, plot_utils

params = ["auc", "c_min", "c_max", "t_half", "t_max", "cl"]

# TODO: Check out documentation for any other arguments that could be interesting (eg. "fixed_columns", etc.)
column_settings = [
    {"df_col": "row_id",
     "id": "row_id"},  # This will be hidden
    # {"df_col": "pmid",
    #  "id": "pmid",
    #  "name": "PMID",},
    {"id": "pmid_hyperlink",
     "type": "text",
     "name": "PMID",
     "presentation": "markdown"},
    {"df_col": "pub_year",
     "id": "pub_year",
     "name": "Year",
     "sortable": True},
    {"id": "drug_hyperlink",
     "type": "text",
     "name": "Drug",
     "presentation": "markdown",},
    {"df_col": "dose",
     "id": "dose",
     "name": "Dose",
     "sortable": True,
     "sort_action": "custom"},
    {"df_col": "gestational_age",
     "id": "gestational_age",
     "name": "Gestational Age",
     "sortable": True},
    {"df_col": "dosing_frequency",
     "id": "dosing_frequency",
     "name": "Frequency",
     "sortable": True},
    {"df_col": "route",
     "id": "route",
     "name": "Route",},
    {"df_col": "c_max",
     "id": "c_max",
     "name": "C_max",
     },
    {"df_col": "auc",
     "id": "auc",
     "name": "AUC",},
    {"df_col": "t_max",
     "id": "t_max",
     "name": "T_max",},
    {"df_col": "t_half",
     "id": "t_half",
     "name": "T_{1/2}",},
    {"df_col": "cl",
     "id": "cl",
     "name": "CL",},
    {"df_col": "c_min",
     "id": "c_min",
     "name": "C_{min}",},
    {"df_col": "reference",
     "id": "reference",
     "name": "Reference",
     "sortable": True,},
    {"df_col": "study_type",
     "id": "study_type",
     "name": "Study Type",
     "sortable": True,},
    {"df_col": "n",
     "id": "n",
     "name": "N",
     "sortable": True,},
]

# Load dropdowns
with open(os.path.join("dropdowns", "drug_dropdown.json"), 'r') as f:
    drug_dropdown = json.load(f)
dropdowns = {
    "drug": drug_dropdown
}

# back_end_column_settings = [
#     {
#         "df_col": f"{param}_stdized_val",
#         "id": f"{param}_stdized_val",
#         "hidden": True,
#      }
#     for param in params] + [
#     {
#         "df_col": f"{param}_dim",
#         "id": f"{param}_dim",
#         "hidden": True,
#      }
#     for param in params]
#
# column_settings = column_settings + back_end_column_settings

server = Flask(__name__)
app = Dash(__name__, server=server)

app.title = "PregPK"
app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        page_layouts.get_navbar(),
        html.Div(id="page-content")
    ],
    className="full-page"
)


@app.callback(
    [Output("dashboard-sidebar", "className"), Output("data_col", "className"),
     Output("dashboard-sidebar-content", "hidden")],
    [Input("collapse-dashboard-sidebar-button", "n_clicks")],
)
def toggle_dashboard_sidebar(n):
    if n and n % 2 == 1:  # Every odd click
        return "sidebar-collapsed", "page-expanded", True  # Collapse the sidebar
    else:  # Every even click
        return "sidebar-expanded", "page-collapsed", False  # Expand the sidebar


@app.callback(
    [Output("drug-filters-collapse", "is_open"), Output("collapse-button-drug-filters", "children")],
    Input("collapse-button-drug-filters", "n_clicks"),
)
def toggle_collapse(n):
    if n % 2 == 1:  # Every odd click
        text = [
            html.Span("Drug", style={"textAlign": "left"}),
            html.Span("\u23f7", style={"textAlign": "right"}),
        ]
        return False, text
    else:
        text = [
            html.Span("Drug", style={"textAlign": "left"}),
            html.Span("\u23f6", style={"textAlign": "right"}),
        ]
        return True, text


@app.callback(
    [Output("disease-filters-collapse", "is_open"), Output("collapse-button-disease-filters", "children")],
    Input("collapse-button-disease-filters", "n_clicks"),
)
def toggle_collapse(n):
    if n % 2 == 1:  # Every odd click
        text = [
            html.Span("Disease/Condition", style={"textAlign": "left"}),
            html.Span("\u23f7", style={"textAlign": "right"}),
        ]
        return False, text
    else:
        text = [
            html.Span("Disease/Condition", style={"textAlign": "left"}),
            html.Span("\u23f6", style={"textAlign": "right"}),
        ]
        return True, text


@app.callback(
    [Output("gest-age-filters-collapse", "is_open"), Output("collapse-button-gest-age-filters", "children")],
    Input("collapse-button-gest-age-filters", "n_clicks"),
)
def toggle_collapse(n):
    if n % 2 == 1:  # Every odd click
        text = [
            html.Span("Gestational Age", style={"textAlign": "left"}),
            html.Span("\u23f7", style={"textAlign": "right"}),
        ]
        return False, text
    else:
        text = [
            html.Span("Gestational Age", style={"textAlign": "left"}),
            html.Span("\u23f6", style={"textAlign": "right"}),
        ]
        return True, text


@app.callback(
    [Output("source-filters-collapse", "is_open"), Output("collapse-button-source-filters", "children")],
    Input("collapse-button-source-filters", "n_clicks"),
)
def toggle_collapse(n):
    if n % 2 == 1:  # Every odd click
        text = [
            html.Span("Source", style={"textAlign": "left"}),
            html.Span("\u23f7", style={"textAlign": "right"}),
        ]
        return False, text
    else:
        text = [
            html.Span("Source", style={"textAlign": "left"}),
            html.Span("\u23f7", style={"textAlign": "right"}),
        ]
        return True, text


@app.callback(
    [Output("plot-options-collapse", "is_open"), Output("collapse-button-plot-options", "children")],
    Input("collapse-button-plot-options", "n_clicks"),
)
def toggle_collapse(n):
    if n % 2 == 1:  # Every odd click
        text = [
            html.Span("Plot Options", style={"textAlign": "left"}),
            html.Span("\u23f7", style={"textAlign": "right"}),
        ]
        return False, text
    else:
        text = [
            html.Span("Plot Options", style={"textAlign": "left"}),
            html.Span("\u23f6", style={"textAlign": "right"}),
        ]
        return True, text


@app.callback(
    [Output("download-options-collapse", "is_open"), Output("collapse-button-download-options", "children")],
    Input("collapse-button-download-options", "n_clicks"),
)
def toggle_collapse(n):
    if n % 2 == 1:  # Every odd click
        text = [
            html.Span("Download", style={"textAlign": "left"}),
            html.Span("\u23f7", style={"textAlign": "right"}),
        ]
        return False, text
    else:
        text = [
            html.Span("Download", style={"textAlign": "left"}),
            html.Span("\u23f6", style={"textAlign": "right"}),
        ]
        return True, text


@app.callback(
    [Output("plot-sidebar", "className"), Output("plot_col", "className"),
     Output("collapse-plot-sidebar-button", "children")],
    [Input("collapse-plot-sidebar-button", "n_clicks")],
)
def toggle_dashboard_sidebar(n):
    if n and n % 2 == 1:  # Every odd click
        return "sidebar-collapsed", "page-expanded", [">>"]  # Collapse the sidebar
    else:  # Every even click
        return "sidebar-expanded", "page-collapsed",  ["<<"]  # Expand the sidebar


# TODO: The filtering, sorting, and plotting functions could be optimized further. Currently, if you do any sorting
#  after filtering, calling the below function will have call on "filter_df()" again, even though none of the filters
#  changed. The obvious solution is to separate the function in two: one that filters and one that sorts, each of which
#  have their own activations (ie. the filtering could run only when filters change). However, given the function is
#  currently designed to start with "df" (the entire imported DataFrame) to start, it is hard to do sorting without
#  filtering first. The alternative would be to use State("table", "data") as an input to the sorting function, but that
#  is a dictionary, and not a DataFrame; so each time a sort is called, a DataFrame would have to be created from the
#  dictionary, and then sorted, which is not efficient. It would be best if the DataFrame for the currently displayed
#  table were stored somewhere that can be accessed by the sorting function; this way, neither filtering nor conversion
#  to a DataFrame has to be done when a sort is called.


@app.callback(
    Output('table', 'data'),
    [Input('study-type-dropdown', 'value'), Input('drug-dropdown', 'value'),
     Input('disease-dropdown', 'value'), Input("gest-age-range-slider", "value"),
     Input('pub-year-range-slider', 'value'), Input('table', 'sort_by')],
    prevent_initial_call=True
)
def update_table(selected_study_types, selected_drugs, selected_diseases,
                 gest_age_range, pub_year_range, sort_by):

    # TODO: Should you add route of administration again??

    filter_dict = {
        "study_type": selected_study_types,
        "drug": selected_drugs,
        "disease_condition": selected_diseases,
        "gest_age_range": gest_age_range,
        "pub_year_range": pub_year_range,
    }

    out_df = data_utils.filter_df(GLOBAL_DF, filter_dict)
    out_df = data_utils.sort_df(out_df, sort_by)

    return out_df[[col["id"] for col in column_settings]].to_dict('records')


@app.callback(
    Output("dashboard-plot", "figure"),
    [Input('table', 'data'), Input('plot-xaxis-dropdown', 'value'), Input('plot-groupby-dropdown', 'value')],
)
def update_dashboard_plot(data, x_axis, group_by):

    # TODO: Review this and make simpler after adding dose and gestational_age

    params = ["auc", "c_min", "c_max", "t_half", "t_max", "cl"]

    # Create lightweight DF only with information that I want to plot
    plot_df = GLOBAL_DF.loc[[i["row_id"] for i in data]][
        ["pmid", "n", "pub_year"] +
        ["gestational_age_stdized_val", "has_non_pregnant", "has_tri_1", "has_tri_2", "has_tri_3", "has_delivery", "has_postpartum"] +
        ["dose_stdized_val", "dose_dim"] +
        [f"{i}_stdized_val" for i in params] + [f"{i}_dim" for i in params]
    ]

    # Filter for most frequent dimensionality
    cols_to_filter_by_dimensionality = params
    if x_axis or group_by == "dose":
        cols_to_filter_by_dimensionality.append("dose")
    for param in params:
        try:
            most_frequent_dim = plot_df[f"{param}_dim"].value_counts().index[0]
            incompatible_idxs = plot_df[plot_df[f"{param}_dim"] != most_frequent_dim].index.tolist()
            plot_df.loc[incompatible_idxs, f"{param}_stdized_val"] = np.nan
        except IndexError:  # Emtpy column
            plot_df.loc[:, f"{param}_stdized_val"] = np.nan

    n_rows = 3
    n_cols = 2
    row_order, col_order = plot_utils.row_and_col_subplot_positions(n_rows, n_cols)
    # TODO: Change figure size to make it look more normal with 3 rows 2 columns
    # TODO: Instead of creating new figure every time, maybe instantiate once in layout and just update them here?
    params_fig = plotly.subplots.make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=("AUC", "C<sub>min</sub>", "C<sub>max</sub>", "T<sub>1/2</sub>", "T<sub>max</sub>", "Clearance"),
        vertical_spacing=0.1, horizontal_spacing=0.1
    )
    params_fig.update_layout(
        height=1000,
        width=800,
    )

    group_args = plot_utils.get_param_plot_group_args(plot_df, x_axis, group_by, n_groups=5)

    # TODO: THIS IS A TEMPORARY FIX. NEED TO UPDATE THIS DYNAMICALLY.
    # y_labels = [r"$\frac{mg*hr}{mL}$", r"$\frac{mg}{mL}$", r"$\frac{mg}{mL}$", r"$hr$", r"$hr$", r"$\frac{mL}{hr}$"]
    y_labels = ["<sup>mg*hr</sup>/<sub>mL</sub>",
                "<sup>mg</sup>/<sub>mL</sub>",
                "<sup>mg</sup>/<sub>mL</sub>",
                "hr",
                "hr",
                "<sup>mL</sup>/<sub>hr</sub>"]

    for i_group, group in enumerate(group_args):
        for i, (plt, ir, ic, y_label) in enumerate(zip(group, row_order, col_order, y_labels)):
            params_fig.add_trace(
                go.Scatter(
                    name=plt["legendgroup"],
                    x=plt["x"],
                    y=plt["y"],
                    legendgroup=plt["legendgroup"],
                    mode="markers",
                    showlegend=i == 0,
                    marker={
                        "color": plt["color"]
                    }
                ),
                row=ir, col=ic,
            )

            if i_group == 0:  # If first group, do formatting

                # X axis label
                if not x_axis:
                    params_fig.update_xaxes(
                        showticklabels=False
                    )
                elif x_axis == "dose":
                    params_fig.update_xaxes(
                        title="Dose (mg)",
                        row=ir, col=ic,
                    )
                elif x_axis == "gestational_age":
                    params_fig.update_xaxes(
                        title="Gestational Age (weeks)",
                        row=ir, col=ic,
                    )

                # Y axis label
                params_fig.update_yaxes(
                    title_text=y_label,
                    title_standoff=5,
                    row=ir, col=ic
                )

    if not group_by:
        params_fig.update_layout(
                showlegend=False,
            )

    return params_fig


@app.callback(
    Output('download-database', 'data'),
    Input('download-button', 'n_clicks'),
    [State('table', 'data')],
    prevent_initial_call=True
)
def download_df(n, data):

    returned_cols = ["pmid", "pub_year", "drug", "dose", "gestational_age", "dosing_frequency",
                     "route", "c_max", "auc", "t_max", "t_half", "cl", "c_min", "reference", "study_type",
                     "n", "gsrs_unii", "atc_code"]

    df = GLOBAL_DF.loc[[i["row_id"] for i in data]][returned_cols]

    csv_string = df.to_csv(index=False)

    return dict(content=csv_string, filename="pregPK.csv", mime_type="text/csv")


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/' or pathname == "/pk-dashboard":
        return page_layouts.dashboard(GLOBAL_DF, column_settings, dropdowns)
    elif pathname == '/about-this-data':
        return page_layouts.plot_page()
    elif pathname in ["/about-us", "/contact"]:
        return page_layouts.under_construction_page()
    else:
        return page_layouts.error_404_page()


if __name__ == "__main__":
    server.run(debug=True, host='0.0.0.0', port=7860)
