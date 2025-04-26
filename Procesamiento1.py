import re
# import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = 'browser'

# def procesar_datos(archivo, inicio, fin):
#     tiempos = []
#     cuentas = []
#     temperaturas = []

#     base_time = None
#     with open(archivo, 'r') as f:
#         lineas = f.readlines()[inicio-1:fin]  # Seleccionar líneas dentro del rango

#     for linea in lineas:
#         match_count = re.search(r'(\d+:\d+:\d+\.\d+) > COUNT1: (\d+)', linea)
#         match_temp = re.search(r'(\d+:\d+:\d+\.\d+) > .*?Temperatura: ([\d\.]+)', linea)

#         if match_count:
#             timestamp, count = match_count.groups()
#             if base_time is None:
#                 base_time = timestamp
#             tiempos.append(timestamp)
#             cuentas.append(int(count))
#             temperaturas.append(None)  # Se mantiene el tamaño de la lista

#         elif match_temp:
#             timestamp, temp = match_temp.groups()
#             if base_time is None:
#                 base_time = timestamp
#             tiempos.append(timestamp)
#             cuentas.append(None)  # Se mantiene el tamaño de la lista
#             temperaturas.append(float(temp))

#     tiempos_relativos = convertir_tiempos_relativos(tiempos)
#     tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas = limpiar_listas(tiempos_relativos, cuentas, temperaturas)

#     return tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas

def procesar_datos(archivo, inicio, fin):
    tiempos = []
    cuentas = []
    temperaturas = []
    
    base_time = None
    with open(archivo, 'r') as f:
        lineas = f.readlines()[inicio-1:fin]  # Seleccionar líneas dentro del rango

    for linea in lineas:
        match_count = re.search(r'(\d+:\d+:\d+\.\d+) > COUNT1: (\d+)', linea)
        match_temp = re.search(r'(\d+:\d+:\d+\.\d+) > Temperatura: ([\d\.]+)', linea)

        if match_count:
            timestamp, count = match_count.groups()
            if base_time is None:
                base_time = timestamp
            tiempos.append(timestamp)
            cuentas.append(int(count))
            temperaturas.append(None)  # Mantener tamaño de array igual

        elif match_temp:
            timestamp, temp = match_temp.groups()
            if base_time is None:
                base_time = timestamp
            tiempos.append(timestamp)
            cuentas.append(None)  # Mantener tamaño de array igual
            temperaturas.append(float(temp))

    # Convertir tiempos a segundos relativos
    tiempos_relativos = convertir_tiempos_relativos(tiempos)

    # Limpiar listas eliminando valores None
    tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas = limpiar_listas(tiempos_relativos, cuentas, temperaturas)

    return tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas

def convertir_tiempos_relativos(tiempos):
    """Convierte los timestamps en segundos relativos al primer dato"""
    from datetime import datetime

    formato = "%H:%M:%S.%f"
    base_time = datetime.strptime(tiempos[0], formato)
    return [(datetime.strptime(t, formato) - base_time).total_seconds() for t in tiempos]

def limpiar_listas(tiempos, cuentas, temperaturas):
    """Elimina valores None y alinea listas"""
    tiempos_filtrados = []
    cuentas_filtradas = []
    temperaturas_filtradas = []

    for i in range(len(tiempos)):
        if cuentas[i] is not None or temperaturas[i] is not None:
            tiempos_filtrados.append(tiempos[i])
            cuentas_filtradas.append(cuentas[i] if cuentas[i] is not None else cuentas_filtradas[-1] if cuentas_filtradas else 0)
            temperaturas_filtradas.append(temperaturas[i] if temperaturas[i] is not None else temperaturas_filtradas[-1] if temperaturas_filtradas else 0)

    return tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas

def graficar_datos(tiempos, cuentas, temperaturas, info):
    fig = go.Figure()

    # Agregar la curva de COUNT1
    fig.add_trace(go.Scatter(
        x=tiempos,
        y=cuentas,
        mode='lines+markers',
        name="Cuentas (COUNT1)",
        line=dict(color="green")
    ))

    # Agregar la curva de Temperatura en el eje Y secundario
    fig.add_trace(go.Scatter(
        x=tiempos,
        y=temperaturas,
        mode='lines+markers',
        name="Temperatura (°C)",
        line=dict(color="orange"),
        yaxis="y2"
    ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=f"{info}",
        xaxis=dict(title="Tiempo (s)"),
        yaxis=dict(
            title=dict(text="Cuentas", font=dict(color="green")),
            tickfont=dict(color="green")
        ),
        yaxis2=dict(
            title=dict(text="Temperatura (°C)", font=dict(color="orange")),
            tickfont=dict(color="orange"),
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0.05, y=0.95),
        template="plotly_white"
    )

    fig.show()

if __name__ == "__main__":
    info = ""
    archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\src\pruebas_15_03_25.txt"  # Cambia esto al nombre de tu archivo
    inicio_linea = 5212           # Línea de inicio
    fin_linea = 5271             # Línea final

    tiempos, cuentas, temperaturas = procesar_datos(archivo_txt, inicio_linea, fin_linea)
    graficar_datos(tiempos, cuentas, temperaturas, info)

    # Guardar los datos en arrays para procesarlos en otro script
    print("Tiempos:", tiempos)
    print("Cuentas:", cuentas)
    print("Temperaturas:", temperaturas)
