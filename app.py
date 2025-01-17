import time
from urllib import request
from flask import request
import dash
from dash import dcc
from dash import html
import numpy as np
from dash.dependencies import Input, Output, State
import json
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from ua_parser import user_agent_parser

import utils.dash_reusable_components as drc
import utils.figures as figs
import utils.bmex as bmex
from utils.bmex_views import *
import utils.views_class as views
import utils.gpe as gpe
import utils.rbm as rbm
from user_agents import parse
from dash import html
from dash.dependencies import Input, Output
import sys

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import random as rand
import h5py
import base64, io
import re
import base64

# instantiates new Dash app
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

# globals
user_agent_string = ''
device_type = ''


# parse the user agent string to detect the device type
def detect_device_type(user_agent_string):
    global device_type
    user_agent = user_agent_parser.Parse(user_agent_string)
    if user_agent['device']['family'] == 'Other':
        device_type = 'desktop'
    else:
        device_type = user_agent['device']['family']
    print(f'This is a {device_type} device.')
    return device_type


# use this function to test device detector function/can use to print device type
def print_device_type_test(user_agent_string_ipad_test):
    global device_type
    user_agent = user_agent_parser.Parse(user_agent_string_ipad_test)
    if user_agent['device']['family'] == 'Other':
        device_type = 'desktop'
    else:
        device_type = user_agent['device']['family']
    print(f'This is a {device_type} device.')
    return device_type


# determines the screen size based on the device type/can specify device parameters for each device
# returns js code created resized div
def resize_screen_user(device_type):
    if device_type == 'desktop':
        width = 500
        height = 500
    elif device_type == 'iPhone':
        width = 375
        height = 667
    elif device_type == 'iPad':
        width = 768
        height = 1024
    else:
        width = 375
        height = 667
    js = f"window.resizeTo({width}, {height});"
    return js


# generates an HTML code snippet that includes a script element with the given
# JavaScript code, which can be appended to the layout of the Dash app to modify its behavior.
def inject_js(js):
    return html.Div(
        children=[
            html.Script(
                children=js,
                type='text/javascript'
            )
        ]
    )


# appends a div element to the app and resizes. does not affect anything else in the app.
def update_display_window():
    global device_type
    js = resize_screen_user(device_type)
    if js:
        app.layout.children.append(inject_js(js))
        print("Window resized successfully!")


# register a callback function to detect the user agent string
@app.callback(
    dash.dependencies.Output('device-type', 'children'),
    [dash.dependencies.Input('url', 'href')]
)
# receives called href as input and returns device type.
def update_device_type(href):
    global user_agent_string
    if not user_agent_string:
        user_agent_string = href
        detect_device_type(user_agent_string)
    return device_type


TAB_STYLE = {
    'width': '72px',
    'border': 'none',
    # 'boxShadow': 'inset 0px -1px 0px 0px lightgrey',
    'background': '#a5b1cd',
    'paddingTop': 0,
    'paddingBottom': 0,
    'height': '60px',
    'font-size': 32,
    'color': '#282b38',
    'borderTop': '3px  #ffffff solid',
}

SELECTED_STYLE = {
    'width': '72px',
    'boxShadow': 'none',
    'borderLeft': '3px #ffffff solid',
    'borderRight': '3px #282b38 solid',
    'borderTop': '3px #ffffff solid',
    'borderBottom': '3px #282b38 solid',
    'background': '#a5b1cd',
    'paddingTop': 0,
    'paddingBottom': 0,
    'height': '60px',
    'font-size': 32,
    'color': '#282b38'
}

app.config.suppress_callback_exceptions = True

app.title = "Bayesian Mass Explorer"

server = app.server

app.layout = html.Div(
    children=[
        dcc.Location(id='url', refresh=False),
        # .container class is fixed, .container.scalable is scalable
        html.Div(
            className="banner",
            children=[
                # Change App Name here
                html.Div(
                    className="container scalable",
                    children=[
                        # Change App Name here
                        html.H2(
                            id="banner-title",
                            children=[
                                html.A(
                                    id="banner-logo",
                                    children=[
                                        html.Img(src=app.get_asset_url("BMEX-logo-3.png"))
                                    ],
                                    href="https://bmex.dev",
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(id='page-content'),
        dcc.Store(id='intermediate-value'),
        dcc.Store(id='nextgraphid', data=2),
        dcc.Store(id='viewsmemory', storage_type='memory',
                  data=json.dumps([{"graphstyle": 'landscape', "quantity": 'BE', "dataset": 'EXP', "colorbar": 'linear',
                                    "wigner": 0, "id": 1,
                                    "ZRange": {"zmin": None, "zmax": None, "protons": 40},
                                    "NRange": {"nmin": None, "nmax": None, "neutrons": 40}}]),
                  ),
        dcc.Store(id='triggerGraph', data=json.dumps("update")),
    ]
)


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if (pathname == "/masses"):
        out = masses_view()
    elif (pathname == "/gpe"):
        out = gpe_view()
    elif (pathname == "/pesnet"):
        out = pesnet_view()
    elif (pathname == "/emulator"):
        out = emu_view()
    else:
        out = html.Div(
            id="body",
            className="container scalable",
            children=[html.P("How did you get here? Click the banner to make it back to safety!")])
    return out


@app.callback(
    [
        Output(component_id='dropdown-select-quantity', component_property='options'),
        # Output(component_id='dropdown-select-quantity', component_property='value'),
        Output(component_id='protons-card', component_property='style'),
        Output(component_id='neutrons-card', component_property='style'),
        # Output(component_id='zmin-card', component_property='style'),
        # Output(component_id='zmax-card', component_property='style'),
        # Output(component_id='nmin-card', component_property='style'),
        # Output(component_id='nmax-card', component_property='style'),
        Output(component_id='colorbar-card', component_property='style'),
        Output(component_id='Wigner-card', component_property='style'),
    ],
    [
        Input(component_id='dropdown-iso-chain', component_property='value'),
        Input('url', 'pathname'),
    ]
)
def quantity_options(is_chain, url):
    show = {'display': 'block'}
    hide = {'display': 'none'}
    if url == "/masses":
        if is_chain == 'single':
            return [[
                # Options for Dropdown
                {"label": "All", "value": "All"},
                {"label": "Binding Energy", "value": "BE"},
                {"label": "One Neutron Separation Energy", "value": "OneNSE", },
                {"label": "One Proton Separation Energy", "value": "OnePSE", },
                {"label": "Two Neutron Separation Energy", "value": "TwoNSE", },
                {"label": "Two Proton Separation Energy", "value": "TwoPSE", },
                {"label": "Alpha Separation Energy", "value": "AlphaSE", },
                {"label": "Two Proton Shell Gap", "value": "TwoNSGap", },
                {"label": "Two Neutron Shell Gap", "value": "TwoPSGap", },
                {"label": "Double Mass Difference", "value": "DoubleMDiff", },
                {"label": "Neutron 3-Point Odd-Even Binding Energy Difference", "value": "N3PointOED", },
                {"label": "Proton 3-Point Odd-Even Binding Energy Difference", "value": "P3PointOED", },
                {"label": "Single-Neutron Energy Splitting", "value": "SNESplitting", },
                {"label": "Single-Proton Energy Splitting", "value": "SPESplitting", },
                {"label": "Wigner Energy Coefficient", "value": "WignerEC", },
            ],
                # Default Value
                # "All",
                # Proton Box Visibility
                show,
                # Neutron Box Visibility
                show,
                # # Zmin Visibility
                # hide,
                # # Zmax Visibility
                # hide,
                # # Nmin Visibility
                # hide,
                # # Nmax Visibility
                # hide,
                # Colorbar Visibility
                hide,
                # Wigner Visibility
                hide,
            ]
        elif is_chain == 'isotopic':
            return [[
                {"label": "Binding Energy", "value": "BE"},
                {"label": "One Neutron Separation Energy", "value": "OneNSE", },
                {"label": "One Proton Separation Energy", "value": "OnePSE", },
                {"label": "Two Neutron Separation Energy", "value": "TwoNSE", },
                {"label": "Two Proton Separation Energy", "value": "TwoPSE", },
                {"label": "Alpha Separation Energy", "value": "AlphaSE", },
                {"label": "Two Proton Shell Gap", "value": "TwoNSGap", },
                {"label": "Two Neutron Shell Gap", "value": "TwoPSGap", },
                {"label": "Double Mass Difference", "value": "DoubleMDiff", },
                {"label": "Neutron 3-Point Odd-Even Binding Energy Difference", "value": "N3PointOED", },
                {"label": "Proton 3-Point Odd-Even Binding Energy Difference", "value": "P3PointOED", },
                {"label": "Single-Neutron Energy Splitting", "value": "SNESplitting", },
                {"label": "Single-Proton Energy Splitting", "value": "SPESplitting", },
                {"label": "Wigner Energy Coefficient", "value": "WignerEC", },
            ],
                # Default Value
                # "BE",
                # Proton Box Visibility
                show,
                # Neutron Box Visibility
                hide,
                # # Zmin Visibility
                # hide,
                # # Zmax Visibility
                # hide,
                # # Nmin Visibility
                # show,
                # # Nmax Visibility
                # show,
                # Colorbar Visibility
                hide,
                # Wigner Visibility
                hide,
            ]
        elif is_chain == 'isotonic':
            return [[
                {"label": "Binding Energy", "value": "BE"},
                {"label": "One Neutron Separation Energy", "value": "OneNSE", },
                {"label": "One Proton Separation Energy", "value": "OnePSE", },
                {"label": "Two Neutron Separation Energy", "value": "TwoNSE", },
                {"label": "Two Proton Separation Energy", "value": "TwoPSE", },
                {"label": "Alpha Separation Energy", "value": "AlphaSE", },
                {"label": "Two Proton Shell Gap", "value": "TwoNSGap", },
                {"label": "Two Neutron Shell Gap", "value": "TwoPSGap", },
                {"label": "Double Mass Difference", "value": "DoubleMDiff", },
                {"label": "Neutron 3-Point Odd-Even Binding Energy Difference", "value": "N3PointOED", },
                {"label": "Proton 3-Point Odd-Even Binding Energy Difference", "value": "P3PointOED", },
                {"label": "Single-Neutron Energy Splitting", "value": "SNESplitting", },
                {"label": "Single-Proton Energy Splitting", "value": "SPESplitting", },
                {"label": "Wigner Energy Coefficient", "value": "WignerEC", },
            ],
                # Default Value
                # "BE",
                # Proton Box Visibility
                hide,
                # Neutron Box Visibility
                show,
                # # Zmin Visibility
                # show,
                # # Zmax Visibility
                # show,
                # # Nmin Visibility
                # hide,
                # # Nmax Visibility
                # hide,
                # Colorbar Visibility
                hide,
                # Wigner Visibility
                hide,
            ]
        elif is_chain == 'landscape':
            return [[
                {"label": "Binding Energy", "value": "BE"},
                {"label": "One Neutron Separation Energy", "value": "OneNSE", },
                {"label": "One Proton Separation Energy", "value": "OnePSE", },
                {"label": "Two Neutron Separation Energy", "value": "TwoNSE", },
                {"label": "Two Proton Separation Energy", "value": "TwoPSE", },
                {"label": "Alpha Separation Energy", "value": "AlphaSE", },
                {"label": "Two Proton Shell Gap", "value": "TwoNSGap", },
                {"label": "Two Neutron Shell Gap", "value": "TwoPSGap", },
                {"label": "Double Mass Difference", "value": "DoubleMDiff", },
                {"label": "Neutron 3-Point Odd-Even Binding Energy Difference", "value": "N3PointOED", },
                {"label": "Proton 3-Point Odd-Even Binding Energy Difference", "value": "P3PointOED", },
                {"label": "Single-Neutron Energy Splitting", "value": "SNESplitting", },
                {"label": "Single-Proton Energy Splitting", "value": "SPESplitting", },
                {"label": "Wigner Energy Coefficient", "value": "WignerEC", },
                {"label": "Quad Def Beta2", "value": "QDB2t", },
            ],
                # Default Value
                # "BE",
                # Proton Box Visibility
                hide,
                # Neutron Box Visibility
                hide,
                # # Zmin Visibility
                # hide,
                # # Zmax Visibility
                # hide,
                # # Nmin Visibility
                # hide,
                # # Nmax Visibility
                # hide,
                # Colorbar Visibility
                show,
                # Wigner Visibility
                show,
            ]
    elif url == "/gpe":
        if is_chain == 'single':
            return [[
                # Options for Dropdown
                # {"label": "All", "value": "All"},
                # {"label": "Binding Energy", "value": "BE"},
                # {"label": "One Neutron Separation Energy", "value": "OneNSE",},
                # {"label": "One Proton Separation Energy", "value": "OnePSE",},
                {"label": "Two Neutron Separation Energy", "value": "TwoNSE", },
                # {"label": "Two Proton Separation Energy", "value": "TwoPSE",},
                # {"label": "Alpha Separation Energy", "value": "AlphaSE",},
                # {"label": "Two Proton Shell Gap", "value": "TwoNSGap",},
                # {"label": "Two Neutron Shell Gap", "value": "TwoPSGap",},
                # {"label": "Double Mass Difference", "value": "DoubleMDiff",},
                # {"label": "Neutron 3-Point Odd-Even Binding Energy Difference", "value": "N3PointOED",},
                # {"label": "Proton 3-Point Odd-Even Binding Energy Difference", "value": "P3PointOED",},
                # {"label": "Single-Neutron Energy Splitting", "value": "SNESplitting",},
                # {"label": "Single-Proton Energy Splitting", "value": "SPESplitting",},
                # {"label": "Wigner Energy Coefficient", "value": "WignerEC",},
            ],
                # Default Value
                # "TwoNSE",
                # Proton Box Visibility
                show,
                # Neutron Box Visibility
                show,
                # Zmin Visibility
                hide,
                # Zmax Visibility
                hide,
                # Nmin Visibility
                hide,
                # Nmax Visibility
                hide,
            ]
        elif is_chain == 'isotopic':
            return [[
                # {"label": "Binding Energy", "value": "BE"},
                # {"label": "One Neutron Separation Energy", "value": "OneNSE",},
                # {"label": "One Proton Separation Energy", "value": "OnePSE",},
                {"label": "Two Neutron Separation Energy", "value": "TwoNSE", },
                # {"label": "Two Proton Separation Energy", "value": "TwoPSE",},
                # {"label": "Alpha Separation Energy", "value": "AlphaSE",},
                # {"label": "Two Proton Shell Gap", "value": "TwoNSGap",},
                # {"label": "Two Neutron Shell Gap", "value": "TwoPSGap",},
                # {"label": "Double Mass Difference", "value": "DoubleMDiff",},
                # {"label": "Neutron 3-Point Odd-Even Binding Energy Difference", "value": "N3PointOED",},
                # {"label": "Proton 3-Point Odd-Even Binding Energy Difference", "value": "P3PointOED",},
                # {"label": "Single-Neutron Energy Splitting", "value": "SNESplitting",},
                # {"label": "Single-Proton Energy Splitting", "value": "SPESplitting",},
                # {"label": "Wigner Energy Coefficient", "value": "WignerEC",},
            ],
                # Default Value
                # "TwoNSE",
                # Proton Box Visibility
                show,
                # Neutron Box Visibility
                hide,
                # Zmin Visibility
                hide,
                # Zmax Visibility
                hide,
                # Nmin Visibility
                hide,
                # Nmax Visibility
                hide,
            ]
        elif is_chain == 'isotonic':
            return [[
                # {"label": "Binding Energy", "value": "BE"},
                # {"label": "One Neutron Separation Energy", "value": "OneNSE",},
                # {"label": "One Proton Separation Energy", "value": "OnePSE",},
                {"label": "Two Neutron Separation Energy", "value": "TwoNSE", },
                # {"label": "Two Proton Separation Energy", "value": "TwoPSE",},
                # {"label": "Alpha Separation Energy", "value": "AlphaSE",},
                # {"label": "Two Proton Shell Gap", "value": "TwoNSGap",},
                # {"label": "Two Neutron Shell Gap", "value": "TwoPSGap",},
                # {"label": "Double Mass Difference", "value": "DoubleMDiff",},
                # {"label": "Neutron 3-Point Odd-Even Binding Energy Difference", "value": "N3PointOED",},
                # {"label": "Proton 3-Point Odd-Even Binding Energy Difference", "value": "P3PointOED",},
                # {"label": "Single-Neutron Energy Splitting", "value": "SNESplitting",},
                # {"label": "Single-Proton Energy Splitting", "value": "SPESplitting",},
                # {"label": "Wigner Energy Coefficient", "value": "WignerEC",},
            ],
                # Default Value
                # "TwoNSE",
                # Proton Box Visibility
                hide,
                # Neutron Box Visibility
                show,
                # Zmin Visibility
                show,
                # Zmax Visibility
                show,
                # Nmin Visibility
                hide,
                # Nmax Visibility
                hide,
            ]


@app.callback(
    [
        Output("viewsmemory", "data"),
        Output("tabs", "children"),
        Output("triggerGraph", "data"),
        Output("tabs", "value"),
        Output("nextgraphid", "data"),
        Output("dropdown-iso-chain", "value"),
        Output("dropdown-select-quantity", "value"),
        Output("dropdown-select-dataset", "value"),
        Output("protons", "value"),
        Output("neutrons", "value"),
        Output("zmin", "value"),
        Output("zmax", "value"),
        Output("nmin", "value"),
        Output("nmax", "value"),
    ],
    [
        State("viewsmemory", "data"),
        State("tabs", "children"),
        # tabs_output
        Input("tabs", "value"),
        # new_plot
        Input("new-button", "n_clicks"),
        State("nextgraphid", "data"),
        # delete_plot
        Input("delete-button", "n_clicks"),
        # reset_page
        Input("reset-button", "n_clicks"),
        # dropdowns
        Input("dropdown-iso-chain", "value"),
        Input("dropdown-select-quantity", "value"),
        Input("dropdown-select-dataset", "value"),
        Input("zmin", "value"),
        Input("zmax", "value"),
        Input("nmin", "value"),
        Input("nmax", "value"),
        Input("protons", "value"),
        Input("neutrons", "value"),
        Input("dropdown-colorbar", "value"),
        Input("radio-wigner", "value"),
    ]
)
def main_update(
        json_cur_views, cur_tabs, tab_n, new_button, graphid,
        delete_button, reset_button, graphstyle, quantity, dataset, zmin,
        zmax, nmin, nmax, protons, neutrons, colorbar, wigner):
    cur_views = json.loads(json_cur_views)
    n = int(tab_n[3])
    # print(base64.urlsafe_b64encode(json_cur_views.encode()).decode())
    print(cur_views[n - 1])

    # tabs_change
    if "tabs" == dash.callback_context.triggered_id:
        print('TABS')
        return [
            json_cur_views,
            cur_tabs,
            json.dumps("dontupdate"),  # graph
            tab_n,
            graphid,
            cur_views[n - 1]['graphstyle'],
            cur_views[n - 1]['quantity'],
            cur_views[n - 1]['dataset'],
            cur_views[n - 1]['ZRange']['protons'],
            cur_views[n - 1]['NRange']['neutrons'],
            cur_views[n - 1]['ZRange']['zmin'],
            cur_views[n - 1]['ZRange']['zmax'],
            cur_views[n - 1]['NRange']['nmin'],
            cur_views[n - 1]['NRange']['nmax'],
        ]

    # new_plot
    if "new-button" == dash.callback_context.triggered_id:
        if len(cur_tabs) > 3 or type(new_button) != type(1):
            raise PreventUpdate
        new_views = cur_views
        default = {"graphstyle": 'landscape', "quantity": 'BE', "dataset": 'EXP', "colorbar": 'linear', "wigner": 0,
                   "id": graphid,
                   "ZRange": {"zmin": None, "zmax": None, "protons": 40},
                   "NRange": {"nmin": None, "nmax": None, "neutrons": 40}}
        new_views.append(default)
        new_tabs = cur_tabs
        new_tabs.append(dcc.Tab(label=str(len(cur_tabs) + 1), value='tab' + str(len(cur_tabs) + 1), style=TAB_STYLE,
                                selected_style=SELECTED_STYLE))
        l = len(new_tabs)
        if graphid == 4:
            graphid = 1
        else:
            graphid += 1
        return [
            json.dumps(new_views),
            new_tabs,
            json.dumps("update"),  # graph
            "tab" + str(l),
            graphid,
            new_views[-1]['graphstyle'],
            new_views[-1]['quantity'],
            new_views[-1]['dataset'],
            new_views[-1]['ZRange']['protons'],
            new_views[-1]['NRange']['neutrons'],
            new_views[-1]['ZRange']['zmin'],
            new_views[-1]['ZRange']['zmax'],
            new_views[-1]['NRange']['nmin'],
            new_views[-1]['NRange']['nmax'],
        ]

    # delete_plot
    if "delete-button" == dash.callback_context.triggered_id:
        if type(delete_button) == type(1) and len(cur_views) > 1:
            new_views = cur_views
            new_views.pop(n - 1)
            new_tabs = cur_tabs
            new_tabs.pop(-1)
            return [
                json.dumps(new_views),
                new_tabs,
                json.dumps("update"),  # graph
                "tab" + str(len(new_views)),
                graphid,
                new_views[-1]['graphstyle'],
                new_views[-1]['quantity'],
                new_views[-1]['dataset'],
                new_views[-1]['ZRange']['protons'],
                new_views[-1]['NRange']['neutrons'],
                new_views[-1]['ZRange']['zmin'],
                new_views[-1]['ZRange']['zmax'],
                new_views[-1]['NRange']['nmin'],
                new_views[-1]['NRange']['nmax'],
            ]
        else:
            raise PreventUpdate

    # reset_page
    if "reset-button" == dash.callback_context.triggered_id:
        new_views = [
            {"graphstyle": 'landscape', "quantity": 'BE', "dataset": 'EXP', "colorbar": 'linear', "wigner": 0, "id": 1,
             "ZRange": {"zmin": None, "zmax": None, "protons": 40},
             "NRange": {"nmin": None, "nmax": None, "neutrons": 40}}]
        return [
            json.dumps(new_views),
            dcc.Tab(label="1", value='tab1', style=TAB_STYLE, selected_style=SELECTED_STYLE),
            json.dumps("update"),  # graph
            'tab1',
            1,
            'landscape',
            'BE',
            'EXP',
            40,
            40,
            None,
            None,
            None,
            None,
        ]

    # dropdown_input
    print('DROPDOWN')
    new_views = cur_views
    if "dropdown-iso-chain" == dash.callback_context.triggered_id:
        new_views[n - 1]['graphstyle'] = graphstyle
    if "dropdown-select-quantity" == dash.callback_context.triggered_id:
        new_views[n - 1]['quantity'] = quantity
        print(new_views[n - 1]['quantity'])
    if "dropdown-select-dataset" == dash.callback_context.triggered_id:
        new_views[n - 1]['dataset'] = dataset
    if "dropdown-colorbar" == dash.callback_context.triggered_id:
        new_views[n - 1]['colorbar'] = colorbar
    if "radio-wigner" == dash.callback_context.triggered_id:
        new_views[n - 1]['wigner'] = wigner
    if "zmin" == dash.callback_context.triggered_id:
        new_views[n - 1]['ZRange']['min'] = zmin
    if "zmax" == dash.callback_context.triggered_id:
        new_views[n - 1]['ZRange']['max'] = zmax
    if "nmin" == dash.callback_context.triggered_id:
        new_views[n - 1]['NRange']['min'] = nmin
    if "nmax" == dash.callback_context.triggered_id:
        new_views[n - 1]['NRange']['max'] = nmax
    if "protons" == dash.callback_context.triggered_id:
        new_views[n - 1]['ZRange']['protons'] = protons
    if "neutrons" == dash.callback_context.triggered_id:
        new_views[n - 1]['NRange']['neutrons'] = neutrons
    return [
        json.dumps(new_views),
        cur_tabs,
        json.dumps("update"),
        tab_n,
        graphid,
        graphstyle,
        quantity,
        dataset,
        protons,
        neutrons,
        zmin,
        zmax,
        nmin,
        nmax
    ]


@app.callback(
    Output("div-graphs", "children"),
    [
        Input("triggerGraph", "data"),
        State("viewsmemory", "data"),
        # Input("graph-chains1", "relayoutData"),
    ],
)
def main_output(
        trigger,
        json_views,
        # relayout_data
):
    if (json.loads(trigger) == "update"):
        output = []
        views_list = json.loads(json_views)  # list of dicts
        print("OUT ", views_list)
        for view_dict in views_list:  # iterate through dicts in list
            view = views.View(view_dict)  # create a view
            output.append(view.plot())
        output.append(html.Button('New Plot', id='new-button', value=None))
        return output
    raise PreventUpdate

    # if "dropdown-iso-chain" == dash.callback_context.triggered_id
    #     outputs = []
    #     for fig in figures:
    #         try:
    #             fig['layout']["xaxis"]["range"] = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
    #             fig['layout']["xaxis"]["autorange"] = False
    #         except (KeyError, TypeError):
    #             fig['layout']["xaxis"]["autorange"] = True

    #         outputs.append(fig)
    #     return outputs


# @app.callback([Output('graph2', 'figure')],
#          [Input('graph', 'relayoutData')], # this triggers the event
#          [State('graph2', 'figure')])
# def zoom_event(relayout_data, *figures):
#     outputs = []
#     for fig in figures:
#         try:
#             fig['layout']["xaxis"]["range"] = [nmin, nmax]
#             fig['layout']["xaxis"]["autorange"] = False
#         except (KeyError, TypeError):
#             fig['layout']["xaxis"]["autorange"] = True

#         outputs.append(fig)

#     return outputs


# t_start = time.time()
#
# NRange, ZRange, N, Z = [None, None, None, None]
#
# np.set_printoptions(precision=5)
# if(chain=='single'):
#     if(N==None or Z==None):
#         return [
#             html.Div(
#                 #id="svm-graph-container",
#                 children=[
#                     html.P("Welcome to Landon's BMEX! Please input your requested nuclei on the left."),
#                 ],
#                 style={'font-size':'3rem'},
#             ),
#         ]
#     elif(quantity == "All"):
#         all_eval = []
#         for name, val in  bmex.__dict__.items():
#             if (callable(val) and name != "OutputString" and name != "GP"):
#                 out_str = bmex.OutputString(name)
#                 result = val(N,Z,dataset)
#                 if isinstance(result,str):
#                     all_eval.append(html.P(result))
#                 else:
#                     all_eval.append(html.P(dataset+" "+out_str+": {:.4f}".format(result)+" MeV"))

#         return [
#             html.Div(
#                 #id="svm-graph-container",
#                 children=all_eval,
#                 style={'font-size':'3rem'},
#             ),
#         ]
#     else:
#         result = getattr(bmex, quantity)(N,Z,dataset)
#         if isinstance(result, str):
#             return [
#                 html.Div(
#                     #id="svm-graph-container",
#                     children=[
#                         html.P(result),
#                     ],
#                     style={'font-size':'3rem'},
#                 ),
#             ]
#         else:
#             out_str = bmex.OutputString(quantity)
#             return [
#                 html.Div(
#                     #id="svm-graph-container",
#                     children=[
#                         html.P(dataset+" "+out_str+": {:.4f}".format(result)+" MeV"),
#                     ],
#                     style={'font-size':'3rem'},
#                 ),
#             ]
# elif chain=="isotopic":
#     if(NRange[0]==None or NRange[1]==None):
#         return [
#             html.Div(
#                 #id="svm-graph-container",
#                 children=[
#                     html.P("Welcome to BMEX! Please input your requested nuclei on the left."),
#                 ],
#                 style={'font-size':'3rem'},
#             ),
#         ]
#     func = getattr(bmex, quantity)
#     out_str = bmex.OutputString(quantity)
#     #& (bmex.df["Z"]==Z1)
#     nmin = bmex.df[(bmex.df["Z"]==Z) & (bmex.df["Model"]==dataset)]['N'].min()
#     nmax = bmex.df[(bmex.df["Z"]==Z) & (bmex.df["Model"]==dataset)]['N'].max()
#     if NRange[0] < nmin:
#         return [
#             html.Div(
#                 id="graph-container",
#                 children=[
#                     html.P("Input value for N Min, "+str(NRange[0])+\
#                         ", is smaller than the minimum N from the data, "+str(nmin)),
#                 ],
#                 style={'font-size':'3rem'},
#             )
#         ]
#     if NRange[1] > nmax:
#         return [
#             html.Div(
#                 id="graph-container",
#                 children=[
#                     html.P("Input value for N Max, "+str(NRange[1])+\
#                         ", is smaller than the maximum N from the data, "+str(nmax)),
#                 ],
#                 style={'font-size':'3rem'},
#             )
#         ]
#     if (NRange[0] >= nmin) and (NRange[1] <= nmax):
#         isotope_chain = figs.isotope_chain(Z, NRange, dataset, out_str, func)
#         return [
#             html.Div(
#                 id="graph-container",
#                 children=dcc.Loading(
#                     className="graph-wrapper",
#                     children=dcc.Graph(id="graph-chains", figure=isotope_chain),
#                 )
#             )
#         ]
# elif chain=="isotonic":
#     if(ZRange[0]==None or ZRange[1]==None):
#         return [
#             html.Div(
#                 #id="svm-graph-container",
#                 children=[
#                     html.P("Welcome to BMEX! Please input your requested nuclei on the left."),
#                 ],
#                 style={'font-size':'3rem'},
#             ),
#         ]
#     func = getattr(bmex, quantity)
#     out_str = bmex.OutputString(quantity)
#     #& (bmex.df["Z"]==Z1)
#     zmin = bmex.df[(bmex.df["N"]==N) & (bmex.df["Model"]==dataset)]["Z"].min()
#     zmax = bmex.df[(bmex.df["N"]==N) & (bmex.df["Model"]==dataset)]["Z"].max()
#     if ZRange[0] < zmin:
#         return [
#             html.Div(
#                 id="graph-container",
#                 children=[
#                     html.P("Input value for Z Min, "+str(ZRange[0])+\
#                         ", is smaller than the minimum Z from the data, "+str(zmin)),
#                 ],
#                 style={'font-size':'3rem'},
#             )
#         ]
#     if ZRange[1] > zmax:
#         return [
#             html.Div(
#                 id="graph-container",
#                 children=[
#                     html.P("Input value for Z Max, "+str(ZRange[1])+\
#                         ", is smaller than the maximum Z from the data, "+str(zmax)),
#                 ],
#                 style={'font-size':'3rem'},
#             )
#         ]
#     if (ZRange[0] >= zmin) and (ZRange[1] <= zmax):
#         isotone_chain = figs.isotone_chain(N, ZRange, dataset, out_str, func)
#         return [
#             html.Div(
#                 id="graph-container",
#                 children=dcc.Loading(
#                     className="graph-wrapper",
#                     children=dcc.Graph(id="graph-chains", figure=isotone_chain),
#                 )
#             )
#         ]
# elif chain=="landscape":
# l = len(graphstyle_arr)
# output = []
# for i in range(l):
#     if i == int(tab_n[3])-1:
#         layout = go.Layout(
#             font={"color": "#a5b1cd"},
#             title=dict(text=bmex.OutputString(quantity_arr[i]), font=dict(size=20)),
#             xaxis=dict(title=dict(text="Neutrons", font=dict(size=20)), gridcolor="#646464", tick0=0, dtick=25, showline=True, #gridcolor="#2f3445",
#             showgrid=True, gridwidth=1, minor=dict(tick0=0, dtick=5, showgrid=True, gridcolor="#3C3C3C",), mirror='ticks', zeroline=False, range=[0,156]),
#             yaxis=dict(title=dict(text="Protons", font=dict(size=20)), gridcolor="#646464", tick0=0, dtick=25, showline=True,
#             showgrid=True, gridwidth=1, minor=dict(tick0=0, dtick=5, showgrid=True, gridcolor="#3C3C3C",), mirror='ticks', zeroline=False, range=[0,104]),
#             #legend=dict(x=0, y=1.05, orientation="h"),
#             #margin=dict(l=100, r=10, t=25, b=40),
#             plot_bgcolor="#282b38",
#             paper_bgcolor="#282b38",
#             #uirevision=model,
#             width=600,
#             height=440,
#         )
#         fig = dcc.Graph(id='graph-chains'+str(i), figure=figs.landscape_plot(dataset_arr[i], layout, quantity_arr[i], colorbar, wigner),
#                 )
#         plots_memory[i] = fig
#         output.append(fig)
#     else:
#         output.append(plots_memory[i])
# output.append(html.Button('New Plot', id='new-plot', value=None))
# #output.append(html.Button('Clone Plot', id='clone-plot', value=None))
# return output

# (1+2*(l-i))/(2*l)-1
# subplots = make_subplots(rows=l, cols=1, subplot_titles=([bmex.OutputString(quantity_arr[k]) for k in range (l)]) )
# for i in range(l):
#     if i == int(tab_n[3])-1:
#         fig = figs.landscape_plot(dataset_arr[i], 1/l, quantity_arr[i], colorbar, wigner)
#         subplots.add_trace(fig, row=i+1, col=1)
#         plots_memory[i] = fig
#     else:
#         subplots.add_trace(plots_memory[i], row=i+1, col=1)
# layout = go.Layout(
#     font={"color": "#a5b1cd"},
#     title=dict(font=dict(size=50)),
#     xaxis=dict(title=dict(text="Neutrons", font=dict(size=50)), gridcolor="#646464", tick0=0, dtick=25, showline=True, #gridcolor="#2f3445",
#     showgrid=True, gridwidth=1, minor=dict(tick0=0, dtick=5, showgrid=True, gridcolor="#3C3C3C",), mirror='ticks', zeroline=False, range=[0,156]),
#     yaxis=dict(title=dict(text="Protons", font=dict(size=50)), gridcolor="#646464", title_font_size=30, tick0=0, dtick=25, showline=True,
#     showgrid=True, gridwidth=1, minor=dict(tick0=0, dtick=5, showgrid=True, gridcolor="#3C3C3C",), mirror='ticks', zeroline=False, range=[0,104]),
#     #legend=dict(x=0, y=1.05, orientation="h"),
#     #margin=dict(l=100, r=10, t=25, b=40),
#     plot_bgcolor="#282b38",
#     paper_bgcolor="#282b38",
#     #uirevision=model,
#     width=600,
#     height=440*l,
#     colorbar=dict(title="", len= 1/l)
# )
# subplots.update_layout(layout)
# output = [dcc.Graph(id="graph-chains", figure=subplots), html.Button('New Plot', id='new-plot', value=None), html.Button('Clone Plot', id='clone-plot', value=None)]
# return output
# return  html.Div(
#             id="graph-container",
#             children=dcc.Loading(
#                 className="graph-wrapper",
#                 children=[dcc.Graph(id="graph-chains"+str(j), figure=land_plot[j]) for j in range(len(graphstyle_arr))].append(html.Button('New Plot', id='new-plot')),
#             )
#         ), html.P("How did you get here? Click the banner to make it back to safety!")

# else:
#     return  [
#         html.Div(
#             id="graph-container",
#             children=dcc.Loading(
#                 className="graph-wrapper",
#                 children=[dcc.Graph(id="graph-chains", figure=land_plot[0]), html.Button('New Plot', id='new-plot')],
#             )
#         )
#     ]

@app.callback(
    Output('intermediate-value', 'data'),
    Output('div-graphs-loading', 'children'),
    Input('submit-gpe', 'n_clicks'),
    [
        State("eta", "value"),
        State("rhon", "value"),
        State("rhoz", "value"),
        State('div-graphs-loading', 'children'),
    ],
    prevent_initial_call=True
)
def update_GP_json(n_clicks, eta, rhon, rhoz, old_out):
    t_start = time.time()
    model = [eta, rhon, rhoz]
    if (model == gpe.default_model):
        return json.dumps(gpe.gp_output.tolist()), [old_out[0]]
    gp_out = gpe.update_GP(model)
    gp_json = json.dumps(gp_out.tolist())
    t_stop = time.time()
    train_out = [html.P("Trained! Took {:.4f} seconds!".format(t_stop - t_start))]
    return gp_json, [old_out[0]] + train_out


# @app.callback(
#     Output('div-graphs-loading', 'children'),
#     Input('submit-gpe', 'n_clicks'),
#     [
#         State("eta","value"),
#         State("rhon","value"),
#         State("rhoz","value"),
#         State('div-graphs-loading','children'),
#     ],
#     prevent_initial_call=True
# )
# def update_GP(n_clicks, eta, rhon, rhoz, old_out):
#     t_start = time.time()

#     model = [eta, rhon, rhoz]
#     gpe.gp_output = gpe.update_GP(model)
#     #gp_json = json.dumps(gp_out.tolist())
#     t_stop = time.time()
#     train_out = [html.P("Trained! Took {:.4f} seconds!".format(t_stop-t_start))]
#     return [old_out[0]] + train_out


@app.callback(
    Output("div-graphs-gpe", "children"),
    [
        Input("dropdown-select-quantity", "value"),
        Input("dropdown-select-dataset", "value"),
        Input("neutrons", "value"),
        Input("protons", "value"),
        Input("dropdown-iso-chain", "value"),
        [Input("nmin", "value"), Input("nmax", "value")],
        [Input("zmin", "value"), Input("zmax", "value")],
        Input("intermediate-value", "data"),
    ],
)
def main_output_gpe(
        quantity,
        dataset,
        N,
        Z,
        chain,
        NRange,
        ZRange,
        gp_json,
):
    t_start = time.time()
    gp_out = np.array(json.loads(gp_json))
    np.set_printoptions(precision=5)
    if (chain == 'single'):
        if (N == None or Z == None):
            return [
                html.Div(
                    # id="svm-graph-container",
                    children=[
                        html.P(
                            "Welcome to the BMEX Gaussian Process Playground! Please input your requested nuclei on the left."),
                    ],
                    style={'font-size': '3rem'},
                ),
            ]
        elif (quantity == "All"):
            all_eval = []
            for name, val in bmex.__dict__.items():
                if (callable(val) and name != "OutputString" and name != "GP"):
                    out_str = bmex.OutputString(name)
                    result = val(N, Z, dataset)
                    if isinstance(result, str):
                        all_eval.append(html.P(result))
                    else:
                        all_eval.append(html.P(dataset + " " + out_str + ": {:.4f}".format(result) + " MeV"))

            return [
                html.Div(
                    # id="svm-graph-container",
                    children=all_eval,
                    style={'font-size': '3rem'},
                ),
            ]
        else:
            result = gpe.gp_single(N, Z, gp_out)
            if isinstance(result, str):
                return [
                    html.Div(
                        # id="svm-graph-container",
                        children=[
                            html.P(result),
                        ],
                        style={'font-size': '3rem'},
                    ),
                ]
            else:
                out_str = bmex.OutputString(quantity)
                return [
                    html.Div(
                        # id="svm-graph-container",
                        children=[
                            html.P(dataset + " " + out_str + ": {:.4f}".format(result[0]) + "±" + "{:.4f}".format(
                                result[1]) + " MeV"),
                        ],
                        style={'font-size': '3rem'},
                    ),
                ]
    elif chain == "isotopic":
        '''
        if(NRange[0]==None or NRange[1]==None and False):
            return [
                html.Div(
                    #id="svm-graph-container",
                    children=[
                        html.P("Welcome to the BMEX Gaussian Process Playground! Please input your requested nuclei on the left."),
                    ],
                    style={'font-size':'3rem'},
                ),
            ]
        '''
        if (Z == None):
            return [
                html.Div(
                    # id="svm-graph-container",
                    children=[
                        html.P(
                            "Welcome to the BMEX Gaussian Process Playground! Please input your requested nuclei on the left."),
                    ],
                    style={'font-size': '3rem'},
                ),
            ]
        # & (bmex.df["Z"]==Z1)
        out_str = "Two Neutron Separation Energy"
        # model = [0.9, 1.529, 0.2533]
        # nmin = bmex.df[(bmex.df["Z"]==Z) & (bmex.df["Model"]==dataset)]['N'].min()
        # nmax = bmex.df[(bmex.df["Z"]==Z) & (bmex.df["Model"]==dataset)]['N'].max()
        '''
        if NRange[0] < nmin:
            return [
                html.Div(
                    id="graph-container",
                    children=[
                        html.P("Input value for N Min, "+str(NRange[0])+\
                            ", is smaller than the minimum N from the data, "+str(nmin)),
                    ],
                    style={'font-size':'3rem'},
                )
            ]
        if NRange[1] > nmax:
            return [
                html.Div(
                    id="graph-container",
                    children=[
                        html.P("Input value for N Max, "+str(NRange[1])+\
                            ", is smaller than the maximum N from the data, "+str(nmax)),
                    ],
                    style={'font-size':'3rem'},
                )
            ]
        '''
        # if (NRange[0] >= nmin) and (NRange[1] <= nmax):
        isotope_chain = gpe.gp_figure_isotopic(Z, out_str, gp_out)
        if isinstance(isotope_chain, str):
            return [
                html.Div(
                    # id="svm-graph-container",
                    children=[
                        html.P(isotope_chain),
                    ],
                    style={'font-size': '3rem'},
                ),
            ]
        else:
            return [
                html.Div(
                    id="graph-container",
                    children=dcc.Loading(
                        className="graph-wrapper",
                        children=dcc.Graph(id="graph-chains", figure=isotope_chain),
                    )
                )
            ]
    elif chain == "isotonic":
        if (ZRange[0] == None or ZRange[1] == None):
            return [
                html.Div(
                    # id="svm-graph-container",
                    children=[
                        html.P("Welcome to BMEX! Please input your requested nuclei on the left."),
                    ],
                    style={'font-size': '3rem'},
                ),
            ]
        func = getattr(bmex, quantity)
        out_str = bmex.OutputString(quantity)
        # & (bmex.df["Z"]==Z1)
        zmin = bmex.df[(bmex.df["N"] == N) & (bmex.df["Model"] == dataset)]["Z"].min()
        zmax = bmex.df[(bmex.df["N"] == N) & (bmex.df["Model"] == dataset)]["Z"].max()
        if ZRange[0] < zmin:
            return [
                html.Div(
                    id="graph-container",
                    children=[
                        html.P("Input value for Z Min, " + str(ZRange[0]) + \
                               ", is smaller than the minimum Z from the data, " + str(zmin)),
                    ],
                    style={'font-size': '3rem'},
                )
            ]
        if ZRange[1] > zmax:
            return [
                html.Div(
                    id="graph-container",
                    children=[
                        html.P("Input value for Z Max, " + str(ZRange[1]) + \
                               ", is smaller than the maximum Z from the data, " + str(zmax)),
                    ],
                    style={'font-size': '3rem'},
                )
            ]
        if (ZRange[0] >= zmin) and (ZRange[1] <= zmax):
            isotone_chain = figs.isotone_chain(N, ZRange, dataset, out_str, func)
            return [
                html.Div(
                    id="graph-container",
                    children=dcc.Loading(
                        className="graph-wrapper",
                        children=dcc.Graph(id="graph-chains", figure=isotone_chain),
                    )
                )
            ]


@app.callback(
    Output("div-graphs-pesnet", "children"),
    [
        Input("dropdown-select-quantity", "value"),
        Input("dropdown-select-dataset", "value"),
        Input("neutrons", "value"),
        Input("protons", "value"),
    ],
)
def main_output_pesnet(
        quantity,
        dataset,
        N,
        Z,
):
    t_start = time.time()
    np.set_printoptions(precision=5)

    infile = "utils/All.dat"

    PESfull = pd.read_csv(infile, delim_whitespace=True, low_memory=False)

    if (N == None or Z == None):
        return [
            html.Div(
                # id="svm-graph-container",
                children=[
                    html.P(
                        "Welcome to the BMEX Potential Energy Surface Generator! Please input your requested nuclei on the left."),
                ],
                style={'font-size': '3rem'},
            ),
        ]
    else:
        pesnet_result = figs.pesnet_surface(N, Z)
        # if(PESfull['A'].isin([N+Z]) and PESfull['Z'].isin([Z])):
        if (not PESfull[(PESfull['A'] == N + Z) & (PESfull['Z'] == Z)].empty):
            true_pes = figs.true_surface(PESfull, N, Z)
            return [
                html.Div(
                    id="graph-container",
                    children=dcc.Loading(
                        className="graph-wrapper",
                        children=[dcc.Graph(id="graph-chains", figure=pesnet_result),
                                  dcc.Graph(id="graph-chains", figure=true_pes)],
                    )
                )
            ]
        else:
            return [
                html.Div(
                    id="graph-container",
                    children=dcc.Loading(
                        className="graph-wrapper",
                        children=dcc.Graph(id="graph-chains", figure=pesnet_result),
                    )
                )
            ]


@app.callback(
    Output("div-emu", "children"),
    [
        Input("dropdown-select-dataset", "value"),
        Input("dropdown-nuc", "value"),
        [Input("Msigma", "value"), Input("Rho", "value"), Input("BE", "value"), \
         Input("Mstar", "value"), Input("K", "value"), Input("zeta", "value"), \
         Input("J", "value"), Input("L", "value"), ],
    ],
)
def main_output_emu(
        dataset,
        nuc,
        NMP,
):
    np.set_printoptions(precision=5)
    nuc_dict = {'16O': 0, '40Ca': 1, '48Ca': 2, '68Ni': 3, '90Zr': 4, '100Sn': 5, '116Sn': 6, '132Sn': 7, '144Sm': 8,
                '208Pb': 9}
    if (None in NMP):
        return [
            html.Div(
                # id="svm-graph-container",
                children=[
                    html.P("Welcome to BMEX! Please input your requested nuclear matter properties on the left!"),
                ],
                style={'font-size': '3rem'},
            ),
        ]
    elif (dataset == "rmf"):
        all_eval = []
        energy, protrad, timing = rbm.rbm_emulator(nuc_dict[nuc], NMP)

        all_eval.append(html.P(nuc + " Emulator Results:"))
        all_eval.append(html.P("Binding Energy: {:.2f} MeV".format(energy)))
        all_eval.append(html.P("Charge Radius:  {:.2f} fm".format(protrad)))
        all_eval.append(html.P("Emulation time: {:.3f} s".format(timing)))

        return [
            html.Div(
                # id="svm-graph-container",
                children=all_eval,
                style={'font-size': '3rem'},
            ),
        ]


# Running the server
if __name__ == "__main__":
    # calls update function to signal if window was resized correctly.
    update_display_window()
    app.run_server(debug=True, dev_tools_ui=True, dev_tools_props_check=False)
