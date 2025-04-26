# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 19:48:21 2024

@author: Pc
"""
import numpy as np
import matplotlib.pyplot as plt

# Reimportar las bibliotecas necesarias después del reinicio
# Definimos los valores del filtro Pi
L = 22e-6  # Inductancia en Henrios
C1 = 4.7e-6  # Capacitancia en Faradios
C2 = 4.7e-6  # Capacitancia en Faradios
R_load = 10  # Resistencia de carga en Ohmios

# Frecuencias de simulación
frequencies = np.logspace(1, 6, 500)  # De 10 Hz a 1 MHz
omega = 2 * np.pi * frequencies  # Frecuencia angular

# Impedancias de los componentes
Z_L = 1j * omega * L  # Impedancia del inductor
Z_C1 = 1 / (1j * omega * C1)  # Impedancia del primer capacitor
Z_C2 = 1 / (1j * omega * C2)  # Impedancia del segundo capacitor

# Impedancia equivalente de los capacitores en paralelo
Z_Ceq = 1 / (1 / Z_C1 + 1 / Z_C2)

# Impedancia total del filtro Pi
Z_total = Z_L + Z_Ceq

# Función de transferencia
H = R_load / (R_load + Z_total)

# Magnitud de la función de transferencia en dB
attenuation_dB = 20 * np.log10(np.abs(H))

# Graficar la respuesta en frecuencia
plt.figure(figsize=(10, 6))
plt.semilogx(frequencies, attenuation_dB, label="Filtro Pi (π)")
plt.axvline(frequencies[np.argmax(np.abs(H) < 1 / np.sqrt(2))], color='r', linestyle='--', 
            label="Frecuencia de corte (-3 dB)")
plt.title("Respuesta de frecuencia del filtro Pi (π)")
plt.xlabel("Frecuencia (Hz)")
plt.ylabel("Ganancia (dB)")
plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.legend()
plt.show()

