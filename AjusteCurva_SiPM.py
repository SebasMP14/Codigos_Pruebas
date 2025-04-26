# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 19:36:44 2024

@author: Pc
"""

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = 'browser'
from scipy.optimize import curve_fit

V_offset = 3.581

# Función para convertir HEX_MAX a voltaje
def hex_to_voltage(hex_value):
    return 21.2 - V_offset + (12 * (255 - hex_value)) / 254

# Datos proporcionados
data = {
    "FF": 0.052, "80": 0.052, "70": 0.052, "60": 0.052, "58": 0.052,
    "54": 0.053, "53": 0.053, "52": 0.054, "51": 0.060, "50": 0.064,
    "4F": 0.069, "4E": 0.073, "4D": 0.078, "4C": 0.084, "4B": 0.090,
    "4A": 0.095, "49": 0.101, "48": 0.107, "47": 0.113, "46": 0.121,
    "45": 0.128, "44": 0.135, "43": 0.141, "42": 0.148, "41": 0.155,
    "40": 0.162
}

# Conversión de datos
hex_values = [int(key, 16) for key in data.keys()]
print("Hex values: ", hex_values)
voltages = [hex_to_voltage(value) for value in hex_values]
voltages[0] = voltages[0] + V_offset
print("\nVoltages: ", voltages)
currents = [value / 1000 for value in data.values()]  # Corriente en microamperios
print("\nCurrents: ", currents)

def diode_model(V, I0, nVt):
    return I0 * np.exp(V / nVt)

# Ajuste de curva
popt, pcov = curve_fit(diode_model, voltages, currents, p0=(1e-6, 0.05))

# Parámetros ajustados
I0, nVt = popt
print(f"I0 (corriente de saturación): {I0:.2e} A")
print(f"nVt (factor térmico): {nVt:.4f} V")

# Curva ajustada
voltages_fit = np.linspace(min(voltages), max(voltages), 500)
currents_fit = diode_model(voltages_fit, *popt)

# Crear la figura
fig = go.Figure()

# Agregar la curva de corriente original
fig.add_trace(go.Scatter(
    x=voltages,
    y=currents,
    mode='lines+markers',
    name='Corriente Original (I)',
    line=dict(color='green'),
    marker=dict(size=6),
    yaxis='y1'
))

# Agregar la curva de corriente filtrada
fig.add_trace(go.Scatter(
    x=voltages_fit,
    y=currents_fit,
    mode='lines+markers',
    name='Curva aproximada (I)',
    line=dict(color='orange'),
    marker=dict(size=6),
    yaxis='y1'
))

# Configuración de los ejes
fig.update_layout(
    title="Curva de Corriente Original y ajustada",
    xaxis=dict(title="Voltaje inverso (V)"),
    yaxis=dict(
        title="Corriente (I) [μA]",
        titlefont=dict(color="green"),
        tickfont=dict(color="green"),
    ),
    legend=dict(x=0.05, y=0.95),
    template="plotly_white"
)

# Mostrar la figura
fig.show()
























