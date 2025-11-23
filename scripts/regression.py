#!/usr/bin/env python3
"""
Script de suporte para Atividade 3.
Lê `data/X.txt` e `data/y.txt`, calcula coeficientes usando fórmula matricial
beta = (X^T X)^{-1} X^T y
Gera `data/regression_plot.json` contendo objeto compatível com Plotly para visualização.

Requisitos: numpy, pandas, plotly
Instale: pip install numpy pandas plotly
"""
import numpy as np
import pandas as pd
import json
import os

def read_vectors():
    x = np.loadtxt('data/X.txt')
    y = np.loadtxt('data/y.txt')
    return x, y

def fit_linear(x, y):
    # Design matrix com intercepto
    X = np.column_stack([np.ones_like(x), x])
    # Beta via fórmula matricial
    beta = np.linalg.inv(X.T @ X) @ X.T @ y
    return beta  # [intercept, slope]

def save_plot(x, y, beta):
    os.makedirs('data', exist_ok=True)
    intercept, slope = float(beta[0]), float(beta[1])
    x_sorted = np.sort(x)
    y_pred = intercept + slope * x_sorted

    data = [
        { 'x': x.tolist(), 'y': y.tolist(), 'mode': 'markers', 'type': 'scatter', 'name': 'Dados' },
        { 'x': x_sorted.tolist(), 'y': y_pred.tolist(), 'mode': 'lines', 'type': 'scatter', 'name': 'Reta estimada' }
    ]
    layout = { 'title': 'Regressão Linear', 'xaxis': {'title': 'Anos de estudo'}, 'yaxis': {'title': 'Salário'} }
    out = {'data': data, 'layout': layout}
    with open('data/regression_plot.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    # Also save a simple HTML file to view standalone
    html = f"""
    <!doctype html>
    <html>
      <head><meta charset='utf-8'><script src='https://cdn.plot.ly/plotly-latest.min.js'></script></head>
      <body>
        <div id='plot' style='width:900px;height:520px'></div>
        <script>
          var obj = {json.dumps(out)};
          Plotly.newPlot('plot', obj.data, obj.layout);
        </script>
      </body>
    </html>
    """
    with open('data/regression_plot.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Gráfico salvo em data/regression_plot.html e data/regression_plot.json')

def main():
    x, y = read_vectors()
    beta = fit_linear(x, y)
    print('Coeficientes: intercept =', beta[0], ', slope =', beta[1])
    save_plot(x, y, beta)

if __name__ == '__main__':
    main()
