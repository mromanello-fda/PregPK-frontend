import os
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
    {"df_col": "drug",
     "id": "drug",
     "name": "Drug",
     "sortable": True,},
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
     "name": "C_{max}",},
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
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    page_layouts.get_navbar(),
    html.Div(id="page-content")
])


@app.callback(
    [Output("dashboard-sidebar", "className"), Output("data_col", "className"),
     Output("dashboard-sidebar-content", "hidden"), Output("collapse-dashboard-sidebar-button", "children")],
    [Input("collapse-dashboard-sidebar-button", "n_clicks")],
)
def toggle_dashboard_sidebar(n):
    if n and n % 2 == 1:  # Every odd click
        return "sidebar-collapsed", "page-expanded", \
               True, [">>", html.Img(src='/assets/filter_icon.png', style={'height': '25px', 'width': 'auto'})]  # Collapse the sidebar
    else:  # Every even click
        return "sidebar-expanded", "page-collapsed", \
               False,  ["<<", html.Img(src='/assets/filter_icon.png', style={'height': '25px', 'width': 'auto'})]  # Expand the sidebar


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
     Input('disease-dropdown', 'value'), Input("gest-age-range-slider", "value"), Input('table', 'sort_by')],
    prevent_initial_call=True
)
def update_table(selected_study_types, selected_drugs, selected_diseases, gest_age_range, sort_by):

    filter_dict = {
        "study_type": selected_study_types,
        "drug": selected_drugs,
        "disease_condition": selected_diseases,
        "gest_age_range": gest_age_range,
    }

    out_df = data_utils.filter_df(GLOBAL_DF, filter_dict)
    out_df = data_utils.sort_df(out_df, sort_by)

    return out_df[[col["id"] for col in column_settings]].fillna("").to_dict('records')


@app.callback(
    Output("dashboard-plot", "figure"),
    [Input('table', 'data'), Input('plot-xaxis-dropdown', 'value')],
)
def update_dashboard_plot(data, x_axis):

    # TODO: Review this and make simpler after adding dose and gestational_age

    params = ["auc", "c_min", "c_max", "t_half", "t_max", "cl"]
    data_df = pd.DataFrame.from_records(data)

    # TODO: Is this unnecessarily memory intensive? Is it better to just filter things again?
    #  Could you add dim to data in table and hide? Would have to convert to pythonic dict first and then deal with that
    #  Maybe find a way to see if this just becomes an image of GLOBAL_DF or whether a new variable is created/saved.
    plot_df = GLOBAL_DF.loc[data_df["row_id"].to_list()]

    most_frequent_dim = dict.fromkeys(params+["dose"])
    for param in most_frequent_dim:
        most_frequent_dim[param] = plot_df[f"{param}_dim"].value_counts().index[0]
        most_frequent_dim["dose"] = plot_df[f"dose_dim"].value_counts().index[0]

    n_rows = 2
    n_cols = 3
    row_order, col_order = plot_utils.row_and_col_subplot_positions(n_rows, n_cols)
    # TODO: Change figure size to make it look more normal with 3 rows 2 columns
    # TODO: Instead of creating new figure every time, maybe instantiate once in layout and just update them here?
    dash_fig = plotly.subplots.make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=("AUC", "C_{min}", "C_{max}", "T_{1/2}", "T_{max}", "Clearance")
    )

    y = [plot_df[plot_df[f"{param}_dim"] == most_frequent_dim[param]][f"{param}_stdized_val"] for param in params]

    if x_axis == "dose":
        x = [plot_df["dose_stdized_val"][i_param.index] for i_param in y]
    elif x_axis == "gestational_age":
        x = [plot_df["gestational_age_stdized_val"][i_param.index] for i_param in y]
    else:
        x = [[0]*len(i_param) for i_param in y]

    # TODO: Quick fix for this; I don't think you should have to reference the objects themselves and then convert them
    #  to base units
    # NOT WORKING: check lithium
    # This might be the worst line of code I've ever written
    units = [f'{(1 * plot_df[plot_df[f"{param}_dim"] == most_frequent_dim[param]][f"{param}_vr"].dropna().iloc[0].unit).to_base_units().units:~}' for param in params]

    title = ["AUC", "CL", "Cmax", "Cmin", "Thalf", "Tmax"]

    # TODO: Things to potentially add:
    #  - markersize depending on N?
    #  - change label/text when hovering to description of publication or data
    #  - change marker label to describe route
    #  - include range/stdev using error bars if available
    #  - change appearance of button that chooses x-axis (gestational age, dose, etc.)

    # TODO: Could structure it in similar way to back-end codes for consistency (plus at the time I had a better
    #  understanding of how to best structure things)

    for i_x, i_y, i_title, i_unit, ir, ic in zip(x, y, title, units, row_order, col_order):
        dash_fig.add_trace(
            go.Scatter(
                x=i_x,
                y=i_y,
                mode="markers",
            ),
            row=ir, col=ic
        )
        dash_fig.update_yaxes(
            title_text=i_unit,
            row=ir, col=ic,
        )
        if x_axis == "dose":
            dash_fig.update_xaxes(
                title_text="Dose",
                row=ir, col=ir
            )
        elif x_axis == "gestational_age":
            dash_fig.update_xaxes(
                title_text="Gestational Age (weeks)",
                row=ir, col=ir
            )
        else:
            dash_fig.update_xaxes(
                title_text="",
                row=ir, col=ir
            )

    dash_fig.update_layout(
        showlegend=False,
    )

    return dash_fig


@app.callback(
    Output("download-database", "data"),
    Input('download-button', 'n_clicks'),
    [State('study-type-dropdown', 'value'), State('drug-dropdown', 'value'), State('disease-dropdown', 'value')],
    prevent_initial_call=True
)
def download_df(n, selected_study_types, selected_drugs, selected_diseases):

    filter_dict = {
        "study_type": selected_study_types,
        "drug": selected_drugs,
        "disease_condition": selected_diseases,
    }

    csv_string = data_utils.filter_df(GLOBAL_DF, filter_dict).to_csv(index=False)

    return dict(content=csv_string, filename="pregPK.csv", mime_type="text/csv")


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return page_layouts.home_page()
    elif pathname == '/pk_dashboard':
        return page_layouts.dashboard(GLOBAL_DF, column_settings)
    elif pathname == '/plots':
        return page_layouts.plot_page()
    elif pathname in ["/about-us", "/contact"]:
        return page_layouts.under_construction_page()
    else:
        return page_layouts.error_404_page()


if __name__ == "__main__":
    server.run(debug=True, host='0.0.0.0', port=7860)
