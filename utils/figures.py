import colorlover as cl
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
import utils.bmex as bmex
from sklearn import metrics
from pickle import dump, load
import tensorflow as tf
from tensorflow.keras import backend as K
import pandas as pd
from dash import html


def single(quantity, model, Z, N, wigner=0):
    if quantity == 'All':
        # return html.P("All")
        output = []
        for qs in bmex.qinput:
            result = bmex.QuanValue(N, Z, model, qs, w=0)
            try:
                result + "a"
            except:
                output.append(html.P(bmex.OutputString(qs) + ": " + str(result) + " MeV"))
            else:
                output.append(html.P(result))
        return html.Div(id="nucleiAll", children=output, style={'font-size': '3rem'})
    # all_eval = []
    #         for name, val in  bmex.__dict__.items():
    #             if (callable(val) and name != "OutputString" and name != "GP"):
    #                 out_str = bmex.OutputString(name)
    #                 result = val(N,Z,dataset)
    #                 if isinstance(result,str):
    #                     all_eval.append(html.P(result))
    #                 else: 
    #                     all_eval.append(html.P(dataset+" "+out_str+": {:.4f}".format(result)+" MeV"))
    else:
        result = bmex.QuanValue(N, Z, model, quantity, w=0)
        try:
            result + "a"
        except:
            return html.P(model + " " + bmex.OutputString(quantity) + ": " + str(result) + " MeV")
        return html.P(result)


def isotopic(quantity, model, colorbar, wigner, ZRange, NRange):
    Z = ZRange['protons']
    Nmin = NRange['nmin']
    Nmax = NRange['nmax']

    if (Nmin == None):
        Nmin = 0
    if (Nmax == None):
        Nmax = 156

    layout = go.Layout(
        # title=f"ROC Curve (AUC = {auc_score:.3f})",
        title=f"Isotopic Chain" + "  -  " + str(model) + "  -  Z = " + str(Z),
        xaxis=dict(title="Neutrons", gridcolor="#2f3445", title_font_size=14),
        yaxis=dict(title=bmex.OutputString(quantity), gridcolor="#2f3445", title_font_size=14),
        # legend=dict(x=0, y=1.05, orientation="h"),
        # margin=dict(l=100, r=10, t=25, b=40),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd", "size": 14},
    )

    neutrons = []
    output = []
    for N in list(range(Nmin, Nmax + 1)):
        q = bmex.QuanValue(N, Z, model, quantity, wigner)
        try:
            q + 1
        except:
            continue
        else:
            neutrons.append(N)
            output.append(q)

    trace0 = go.Scatter(
        x=neutrons, y=output, mode="lines+markers", name="Test Data", marker= \
            {
                "color": "#13c6e9",
                # "size": 20,
            }
    )

    # figure = px.line(x=Z, y=output, markers=True)
    data = [trace0]
    figure = go.Figure(data=data, layout=layout)
    figure.update_xaxes(title_font_size=20)
    figure.update_yaxes(title_font_size=20)
    figure.update_layout(title_font_size=24)
    return figure


def isotonic(quantity, model, colorbar, wigner, ZRange, NRange):
    N = NRange['neutrons']
    Zmin = ZRange['zmin']
    Zmax = ZRange['zmax']

    if (Zmin == None):
        Zmin = 0
    if (Zmax == None):
        Zmax = 106

    layout = go.Layout(
        # title=f"ROC Curve (AUC = {auc_score:.3f})",
        title=f"Isotonic Chain" + "  -  " + str(model) + "  -  N = " + str(N),
        xaxis=dict(title="Protons", gridcolor="#2f3445", title_font_size=14),
        yaxis=dict(title=bmex.OutputString(quantity), gridcolor="#2f3445", title_font_size=14),
        # legend=dict(x=0, y=1.05, orientation="h"),
        # margin=dict(l=100, r=10, t=25, b=40),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd", "size": 14},
    )

    protons = []
    output = []
    for Z in list(range(Zmin, Zmax + 1)):
        q = bmex.QuanValue(N, Z, model, quantity, wigner)
        try:
            q + 1
        except:
            continue
        else:
            protons.append(Z)
            output.append(q)

    trace0 = go.Scatter(
        x=protons, y=output, mode="lines+markers", name="Test Data", marker= \
            {
                "color": "#13c6e9",
                # "size": 20,
            }
    )

    # figure = px.line(x=Z, y=output, markers=True)
    data = [trace0]
    figure = go.Figure(data=data, layout=layout)
    figure.update_xaxes(title_font_size=20)
    figure.update_yaxes(title_font_size=20)
    figure.update_layout(title_font_size=24)
    return figure


def landscape(quantity, model, colorbar, wigner, ZRange=None, NRange=None):
    layout = go.Layout(
        font={"color": "#a5b1cd"},
        title=dict(text=bmex.OutputString(quantity) + "   -   " + str(model), font=dict(size=20)),
        xaxis=dict(title=dict(text="Neutrons", font=dict(size=20)), gridcolor="#646464", tick0=0, dtick=25,
                   showline=True,  # gridcolor="#2f3445",
                   showgrid=True, gridwidth=1, minor=dict(tick0=0, dtick=5, showgrid=True, gridcolor="#3C3C3C", ),
                   mirror='ticks', zeroline=False, range=[0, 156]),
        yaxis=dict(title=dict(text="Protons", font=dict(size=20)), gridcolor="#646464", tick0=0, dtick=25,
                   showline=True,
                   showgrid=True, gridwidth=1, minor=dict(tick0=0, dtick=5, showgrid=True, gridcolor="#3C3C3C", ),
                   mirror='ticks', zeroline=False, range=[0, 104]),
        # legend=dict(x=0, y=1.05, orientation="h"),
        # margin=dict(l=100, r=10, t=25, b=40),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        # uirevision=model,
        width=600,
        height=440,
    )

    step = 2

    values = np.full((200 // step, 350 // step), None)
    for Z in range(2, 105, step):
        chain = bmex.IsotopicChain(Z, model, quantity, step, wigner)
        for N in chain["N"]:
            values[Z // 2, N // 2] = chain[chain["N"] == N].iloc[0, 0]

    filtered = []
    for e in values.flatten():
        try:
            e + 0.0
        except:
            pass
        else:
            filtered.append(e)
    filtered = np.array(filtered)
    max_z = float(np.percentile(filtered, [97]))
    equalized_color = filtered[filtered >= 0]
    equalized_color = equalized_color[equalized_color <= max_z]

    def cb(colorbar):
        if (colorbar == 'linear'):
            return [
                [0, 'rgb(0, 0, 0)'],
                [.01, 'rgb(127, 0, 255)'],
                [.2, 'rgb(0, 0, 255)'],
                [.39, 'rgb(0, 255, 127)'],
                [.58, 'rgb(127, 255, 0)'],
                [.76, 'rgb(255, 255, 0)'],
                [.95, 'rgb(255, 128, 0)'],
                [1, 'rgb(255, 0, 0)'],
            ]
        elif (colorbar == 'equal'):
            range_z = max(equalized_color) - min(equalized_color)
            scale = (np.percentile(equalized_color, [19 * x for x in range(1, 6)])) / range_z
            return [
                [0, 'rgb(0, 0, 0)'],
                [.01, 'rgb(127, 0, 255)'],
                [scale[0], 'rgb(0, 0, 255)'],
                [scale[1], 'rgb(0, 255, 127)'],
                [scale[2], 'rgb(127, 255, 0)'],
                [scale[3], 'rgb(255, 255, 0)'],
                [scale[4], 'rgb(255, 128, 0)'],
                [1, 'rgb(255, 0, 0)'],
            ]
        elif (colorbar == 'monochrome'):
            return [[0, 'rgb(230, 120, 85)'], [1, 'rgb(255, 255, 255)']]

    trace = go.Heatmap(
        x=np.arange(2, 155, step), y=np.arange(2, 105, step), z=values,
        zmin=0, zmax=max_z, name="",
        colorscale=cb(colorbar),
        colorbar=dict(
            title="",
            # len=,
            # y=cb_y
            # tick0= 0,
            # tickmode= 'array',
            # tickvals= [-2, 0, 2, 4, 6],
            # ticktext= ["<0", "0", "2", "4", "6"],
        ),
        hovertemplate='<b><i>N</i></b>: %{x}<br>' +
                      '<b><i>Z</i></b>: %{y}<br>' +
                      '<b><i>Value</i></b>: %{z}',
    )

    return go.Figure(data=[trace], layout=layout)


def serve_prediction_plot(
        model, X_train, X_test, y_train, y_test, Z, xx, yy, mesh_step, threshold
):
    # Get train and test score from model
    y_pred_train = (model.decision_function(X_train) > threshold).astype(int)
    y_pred_test = (model.decision_function(X_test) > threshold).astype(int)
    train_score = metrics.accuracy_score(y_true=y_train, y_pred=y_pred_train)
    test_score = metrics.accuracy_score(y_true=y_test, y_pred=y_pred_test)

    # Compute threshold
    scaled_threshold = threshold * (Z.max() - Z.min()) + Z.min()
    range = max(abs(scaled_threshold - Z.min()), abs(scaled_threshold - Z.max()))

    # Colorscale
    bright_cscale = [[0, "#ff3700"], [1, "#0b8bff"]]
    cscale = [
        [0.0000000, "#ff744c"],
        [0.1428571, "#ff916d"],
        [0.2857143, "#ffc0a8"],
        [0.4285714, "#ffe7dc"],
        [0.5714286, "#e5fcff"],
        [0.7142857, "#c8feff"],
        [0.8571429, "#9af8ff"],
        [1.0000000, "#20e6ff"],
    ]

    # Create the plot
    # Plot the prediction contour of the SVM
    trace0 = go.Contour(
        x=np.arange(xx.min(), xx.max(), mesh_step),
        y=np.arange(yy.min(), yy.max(), mesh_step),
        z=Z.reshape(xx.shape),
        zmin=scaled_threshold - range,
        zmax=scaled_threshold + range,
        hoverinfo="none",
        showscale=False,
        contours=dict(showlines=False),
        colorscale=cscale,
        opacity=0.9,
    )

    # Plot the threshold
    trace1 = go.Contour(
        x=np.arange(xx.min(), xx.max(), mesh_step),
        y=np.arange(yy.min(), yy.max(), mesh_step),
        z=Z.reshape(xx.shape),
        showscale=False,
        hoverinfo="none",
        contours=dict(
            showlines=False, type="constraint", operation="=", value=scaled_threshold
        ),
        name=f"Threshold ({scaled_threshold:.3f})",
        line=dict(color="#708090"),
    )

    # Plot Training Data
    trace2 = go.Scatter(
        x=X_train[:, 0],
        y=X_train[:, 1],
        mode="markers",
        name=f"Training Data (accuracy={train_score:.3f})",
        marker=dict(size=10, color=y_train, colorscale=bright_cscale),
    )

    # Plot Test Data
    trace3 = go.Scatter(
        x=X_test[:, 0],
        y=X_test[:, 1],
        mode="markers",
        name=f"Test Data (accuracy={test_score:.3f})",
        marker=dict(
            size=10, symbol="triangle-up", color=y_test, colorscale=bright_cscale
        ),
    )

    layout = go.Layout(
        xaxis=dict(ticks="", showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(ticks="", showticklabels=False, showgrid=False, zeroline=False),
        hovermode="closest",
        legend=dict(x=0, y=-0.01, orientation="h"),
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd"},
    )

    data = [trace0, trace1, trace2, trace3]
    figure = go.Figure(data=data, layout=layout)

    return figure


def isotope_chain_go(Z, NRange, model, axis_label, func):
    output = []

    for i in NRange:
        output.append(func(i, Z, model))

    trace0 = go.Scatter(
        x=NRange, y=output, mode="lines", name="Test Data", marker={"color": "#13c6e9"}
    )

    layout = go.Layout(
        # title=f"ROC Curve (AUC = {auc_score:.3f})",
        title=f"Isotopic Chain",
        xaxis=dict(title="Neutrons", gridcolor="#2f3445"),
        yaxis=dict(title=axis_label, gridcolor="#2f3445"),
        # legend=dict(x=0, y=1.05, orientation="h"),
        # margin=dict(l=100, r=10, t=25, b=40),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd"},
    )

    data = [trace0]
    figure = go.Figure(data=data, layout=layout)

    return figure


def R2(y_true, y_pred):
    SS_res = K.sum(K.square(y_true - y_pred))
    SS_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - SS_res / (SS_tot + K.epsilon()))


def PESpredict_single(A, Z, Q20, Q30, model, scaler):
    X = np.zeros(4)
    X[0] = A
    X[1] = Z
    X[2] = Q20
    X[3] = Q30
    xx = scaler.transform(X.reshape(1, -1))
    pes = model.predict(xx)

    return pes.T.squeeze()


def PESpredict(X, model, scaler):
    xx = scaler.transform(X)
    pes = model.predict(xx)

    return pes.T.squeeze()


def pesnet_surface(N, Z):
    model = tf.keras.models.load_model('utils/PESNet.model', custom_objects={'R2': R2})
    xscaler = load(open('utils/xscaler.pkl', "rb"))

    An = N + Z
    q20num = 121
    q30num = 21
    Q20 = np.linspace(0, 250, q20num)
    Q30 = np.linspace(0, 60, q30num)
    Q20v, Q30v = np.meshgrid(Q20, Q30, indexing='ij')
    Q20v = Q20v.flatten()
    Q30v = Q30v.flatten()
    Av = np.zeros(Q20v.shape)
    Zv = np.zeros(Q20v.shape)
    Av[:] = An
    Zv[:] = Z
    # xx = (Q20,Q30)
    # PESv = np.vectorize(PESpredict)
    # pes = PESv(A, Z, Q20v, Q30v, model, xscaler)
    X = (Av, Zv, Q20v, Q30v)
    X = np.asarray(X)
    X = X.T

    pes = np.reshape(PESpredict(X, model, xscaler), (q20num, q30num)).T

    layout = go.Layout(
        # title=f"ROC Curve (AUC = {auc_score:.3f})",
        title=f"PESnet Prediction",
        xaxis=dict(title="Q20", gridcolor="#2f3445", title_font_size=14),
        yaxis=dict(title="Q30", gridcolor="#2f3445", title_font_size=14),
        # legend=dict(x=0, y=1.05, orientation="h"),
        # margin=dict(l=100, r=10, t=25, b=40),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd", "size": 28},
    )

    fig = go.Figure(data=
    go.Contour(
        z=pes,
        x=Q20,  # horizontal axis
        y=Q30,  # vertical axis
        colorscale="Spectral_r",
    ), layout=layout)
    return fig


def true_surface(df, N, Z):
    An = N + Z
    q20num = 126
    q30num = 21
    Q20 = np.linspace(0, 250, q20num)
    Q30 = np.linspace(0, 60, q30num)
    Q20v, Q30v = np.meshgrid(Q20, Q30, indexing='ij')
    Q20v = Q20v.flatten()
    Q30v = Q30v.flatten()
    Av = np.zeros(Q20v.shape)
    Zv = np.zeros(Q20v.shape)
    Av[:] = An
    Zv[:] = Z
    # xx = (Q20,Q30)
    # PESv = np.vectorize(PESpredict)
    # pes = PESv(A, Z, Q20v, Q30v, model, xscaler)
    PES_sub = df[(df['A'] == An) & (df['Z'] == Z)]

    A = PES_sub['A']
    Z = PES_sub['Z']
    # Q20 = PES_sub['Q20']
    # Q30 = PES_sub['Q30']
    E = PES_sub['HFB_cubic']

    layout = go.Layout(
        # title=f"ROC Curve (AUC = {auc_score:.3f})",
        title=f"True PES",
        xaxis=dict(title="Q20", gridcolor="#2f3445", title_font_size=14),
        yaxis=dict(title="Q30", gridcolor="#2f3445", title_font_size=14),
        # legend=dict(x=0, y=1.05, orientation="h"),
        # margin=dict(l=100, r=10, t=25, b=40),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd", "size": 28},
    )

    fig = go.Figure(data=
    go.Contour(
        z=np.reshape(E.to_numpy(), (q20num, q30num)).T,
        x=Q20,  # horizontal axis
        y=Q30,  # vertical axis
        colorscale="Spectral_r",
    ), layout=layout)
    return fig


def isotope_chain_gp(Z, NRange, model, axis_label, func):
    output = []

    layout = go.Layout(
        # title=f"ROC Curve (AUC = {auc_score:.3f})",
        title=f"Isotopic Chain",
        xaxis=dict(title="Neutrons", gridcolor="#2f3445", title_font_size=14),
        yaxis=dict(title=axis_label, gridcolor="#2f3445", title_font_size=14),
        # legend=dict(x=0, y=1.05, orientation="h"),
        # margin=dict(l=100, r=10, t=25, b=40),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd", "size": 14},
    )

    N = bmex.df[
        (bmex.df["Z"] == Z) & (bmex.df["Model"] == "Exp") & (bmex.df["N"] >= NRange[0]) & (bmex.df["N"] <= NRange[1])][
        "N"]
    plotFRDMGP, plotFRDMGPBandplus, plotFRDMGPBandminus = func(model[0], model[1], model[2], Z)

    trace0 = go.Scatter(
        x=N, y=plotFRDMGP, mode="lines+markers", name="Test Data", marker= \
            {
                "color": "#13c6e9",
                # "size": 20,
            }
    )

    # figure = px.line(x=Z, y=output, markers=True)
    data = [trace0]
    figure = go.Figure([
        go.Scatter(
            x=plotFRDMGP.T[0],
            y=plotFRDMGP.T[1],
            line=dict(color='rgb(100,100,80)'),
            mode='lines'
        ),
        go.Scatter(
            x=plotFRDMGP.T[0] + plotFRDMGP.T[0][::-1],  # x, then x reversed
            y=plotFRDMGPBandplus.T[0] + plotFRDMGPBandminus.T[1][::-1],  # upper, then lower reversed
            fill='toself',
            fillcolor='rgba(255,0,0)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            # showlegend=False
        )
    ], layout=layout)
    figure.update_xaxes(title_font_size=20)
    figure.update_yaxes(title_font_size=20)
    figure.update_layout(title_font_size=24)
    return figure


def isotone_chain_go(N, ZRange, model, axis_label, func):
    output = []

    for i in ZRange:
        output.append(func(N, i, model))

    trace0 = go.Scatter(
        x=ZRange, y=output, mode="lines", name="Test Data", marker={"color": "#13c6e9"}
    )

    layout = go.Layout(
        # title=f"ROC Curve (AUC = {auc_score:.3f})",
        title=f"Isotonic Chain",
        xaxis=dict(title="Protons", gridcolor="#2f3445"),
        yaxis=dict(title=axis_label, gridcolor="#2f3445"),
        # legend=dict(x=0, y=1.05, orientation="h"),
        # margin=dict(l=100, r=10, t=25, b=40),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd"},
    )

    data = [trace0]
    figure = go.Figure(data=data, layout=layout)

    return figure


def serve_pie_confusion_matrix(model, X_test, y_test, Z, threshold):
    # Compute threshold
    scaled_threshold = threshold * (Z.max() - Z.min()) + Z.min()
    y_pred_test = (model.decision_function(X_test) > scaled_threshold).astype(int)

    matrix = metrics.confusion_matrix(y_true=y_test, y_pred=y_pred_test)
    tn, fp, fn, tp = matrix.ravel()

    values = [tp, fn, fp, tn]
    label_text = ["True Positive", "False Negative", "False Positive", "True Negative"]
    labels = ["TP", "FN", "FP", "TN"]
    blue = cl.flipper()["seq"]["9"]["Blues"]
    red = cl.flipper()["seq"]["9"]["Reds"]
    colors = ["#13c6e9", blue[1], "#ff916d", "#ff744c"]

    trace0 = go.Pie(
        labels=label_text,
        values=values,
        hoverinfo="label+value+percent",
        textinfo="text+value",
        text=labels,
        sort=False,
        marker=dict(colors=colors),
        insidetextfont={"color": "white"},
        rotation=90,
    )

    layout = go.Layout(
        title="Confusion Matrix",
        margin=dict(l=50, r=50, t=100, b=10),
        legend=dict(bgcolor="#282b38", font={"color": "#a5b1cd"}, orientation="h"),
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font={"color": "#a5b1cd"},
    )

    data = [trace0]
    figure = go.Figure(data=data, layout=layout)

    return figure
