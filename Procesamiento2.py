import re
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
from scipy.interpolate import UnivariateSpline, griddata

pio.renderers.default = 'browser'

def procesar_datos(archivo, inicio, fin):
    tiempos = []
    cuentas = []
    temperaturas = []
    interrupciones = []  
    
    base_time = None
    base_time1 = None
    interrupcion_iniciada = False
    t_inicio = None

    with open(archivo, 'r') as f:
        lineas = f.readlines()[inicio-1:fin]

    for linea in lineas:
        match_count = re.search(r'([\d:]+\.\d+) > COUNT1: (\d+)', linea)
        match_temp = re.search(r'([\d:]+\.\d+) > .*Temperatura: ([\d\.]+)', linea)
        match_combined = re.search(r'([\d:]+\.\d+) > millis: .*? Temperatura: ([\d\.]+)', linea)
        match_inicio = re.search("Interrupci", linea)
        match_fin = re.search("(polarization_settling) -> Vbias:", linea)
        
        
        # Verificar si la línea contiene los mensajes de interrupción
        if match_inicio:
            match_inicio = re.search(r'([\d:]+\.\d+)', linea)
            if match_inicio:
                t_inicio = match_inicio.group(1)
                if base_time1 is None:
                    base_time1 = datetime.strptime(t_inicio, "%H:%M:%S.%f")
                t_inicio = (datetime.strptime(t_inicio, "%H:%M:%S.%f") - base_time1).total_seconds()
                interrupcion_iniciada = True

        if match_fin and interrupcion_iniciada:
            match_fin = re.search(r'([\d:]+\.\d+)', linea)
            if match_fin:
                t_fin = match_fin.group(1)
                t_fin = (datetime.strptime(t_fin, "%H:%M:%S.%f") - base_time1).total_seconds()
                interrupciones.append([t_inicio, t_fin])  # Guardamos el intervalo
                interrupcion_iniciada = False  # Termina la interrupción
        elif match_fin:                                                        #### para cuando hay dos canales con compensacion...
            match_fin = re.search(r'([\d:]+\.\d+)', linea)
            if match_fin:
                t_fin = match_fin.group(1)
                t_fin = (datetime.strptime(t_fin, "%H:%M:%S.%f") - base_time1).total_seconds()
                interrupciones[-1][-1] = t_fin  # Guardamos el intervalo
                interrupcion_iniciada = False   # Termina la interrupción
        
        if match_count:
            timestamp, count = match_count.groups()
            if base_time is None:
                base_time = timestamp
                base_time1 = datetime.strptime(timestamp, "%H:%M:%S.%f")
            tiempos.append(timestamp)
            cuentas.append(int(count))
            temperaturas.append(None)

        elif match_temp:
            timestamp, temp = match_temp.groups()
            if base_time is None:
                base_time = timestamp
            tiempos.append(timestamp)
            cuentas.append(None)
            temperaturas.append(float(temp))

        elif match_combined:
            timestamp, temp = match_combined.groups()
            if base_time is None:
                base_time = timestamp
            tiempos.append(timestamp)
            cuentas.append(None)
            temperaturas.append(float(temp))
    
    tiempos_relativos = convertir_tiempos_relativos(tiempos)
    tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas = limpiar_listas(tiempos_relativos, cuentas, temperaturas)
    return tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas, interrupciones

def convertir_tiempos_relativos(tiempos):
    formato = "%H:%M:%S.%f"
    base_time = datetime.strptime(tiempos[0], formato)
    return [(datetime.strptime(t, formato) - base_time).total_seconds() for t in tiempos]

def limpiar_listas(tiempos, cuentas, temperaturas):
    tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas = [], [], []
    for i in range(len(tiempos)):
        if cuentas[i] is not None or temperaturas[i] is not None:
            tiempos_filtrados.append(tiempos[i])
            cuentas_filtradas.append(cuentas[i] if cuentas[i] is not None else cuentas_filtradas[-1] if cuentas_filtradas else 0)
            temperaturas_filtradas.append(temperaturas[i] if temperaturas[i] is not None else temperaturas_filtradas[-1] if temperaturas_filtradas else 0)
    return tiempos_filtrados, cuentas_filtradas, temperaturas_filtradas

def calcular_tasa_y_temperatura(tiempos, cuentas, temperaturas, delta_t):
    """Calcula la tasa de impactos y la temperatura promedio en intervalos de tiempo."""
    cuentas_tasa = []
    tiempos_prom = []
    i = 0
    while i < len(tiempos) - 1:
        t1 = tiempos[i]
        ind_t2 = i
        while ind_t2 < len(tiempos) and tiempos[ind_t2] - t1 < delta_t:
            ind_t2 += 1
        
        if ind_t2 < len(tiempos):
            t2 = tiempos[ind_t2]
            impactos_intervalo = max(0, cuentas[ind_t2] - cuentas[i])
            tasa_impactos = impactos_intervalo / (t2 - t1)
            cuentas_tasa.append(tasa_impactos)
            tiempos_prom.append((t1 + t2) / 2)
        
        i = ind_t2
    
    temperaturas_filtradas = np.interp(tiempos_prom, tiempos, temperaturas)
    return tiempos_prom, cuentas_tasa, temperaturas_filtradas

def graficar_metodo_1(tiempos, cuentas, temperaturas, interrupciones, info):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tiempos, y=cuentas, mode='lines+markers', name="Cuentas (COUNT1)", line=dict(color="green")))
    fig.add_trace(go.Scatter(x=tiempos, y=temperaturas, mode='lines+markers', name="Temperatura (°C)", line=dict(color="orange"), yaxis="y2"))
    # Graficar las interrupciones con líneas verticales
    for i, (inicio, fin) in enumerate(interrupciones):
        if i == 0:
            fig.add_trace(go.Scatter(
                x=[inicio, inicio], y=[min(cuentas), max(cuentas)],
                mode="lines", line=dict(color="red", dash="dot"),
                name="Inicio de interrupción"
            ))

            fig.add_trace(go.Scatter(
                x=[fin, fin], y=[min(cuentas), max(cuentas)],
                mode="lines", line=dict(color="blue", dash="dot"),
                name="Fin de interrupción"
            ))
        else: 
            fig.add_trace(go.Scatter(
                x=[inicio, inicio], y=[min(cuentas), max(cuentas)],
                mode="lines", line=dict(color="red", dash="dot"),
                showlegend=False
            ))

            # Línea de fin (azul)
            fig.add_trace(go.Scatter(
                x=[fin, fin], y=[min(cuentas), max(cuentas)],
                mode="lines", line=dict(color="blue", dash="dot"),
                showlegend=False
            ))
    fig.update_layout(
        title=info,
        xaxis=dict(title="Tiempo (s)"),
        yaxis=dict(title="Cuentas", tickfont=dict(color="green")),
        yaxis2=dict(title="Temperatura (°C)", tickfont=dict(color="orange"), overlaying="y", side="right"),
        template="plotly_white"
    )
    fig.show()

def graficar_metodo_2(cuentas, temperaturas):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=temperaturas, y=cuentas, mode='markers', name="COUNT1 vs Temperatura", marker=dict(color='green')))
    fig.update_layout(title="COUNT1 vs Temperatura", xaxis=dict(title="Temperatura (°C)"), yaxis=dict(title="Cuentas (COUNT1)"), template="plotly_white")
    fig.show()

def graficar_metodo_3(tiempos, cuentas, temperaturas):
    derivadas = np.gradient(cuentas, tiempos)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=temperaturas, y=derivadas, mode='lines+markers', name="dCOUNT/dt vs Temperatura", line=dict(color="red")))
    fig.update_layout(title="Tasa de impactos vs Temperatura", xaxis=dict(title="Temperatura (°C)"), yaxis=dict(title="Tasa de cambios (dCOUNT/dt)"), template="plotly_white")
    fig.show()


def graficar_metodo_4(tiempos, cuentas, temperaturas, delta_t):
    import plotly.graph_objects as go
    import numpy as np
    
    # Calcular la cantidad de impactos en cada intervalo de tiempo
    impactos = np.diff(cuentas, prepend=cuentas[0])
    impactos[impactos < 0] = 0  # Asegurar que solo cuente aumentos

    # Calcular COUNT/delta_t
    cuentas_tasa = []
    tiempos_prom = []
    for i in range(0, len(tiempos), delta_t):
        if i + delta_t < len(tiempos):
            suma_impactos = sum(impactos[i:i + delta_t])
            cuentas_tasa.append(suma_impactos / (tiempos[i + delta_t] - tiempos[i]))
            tiempos_prom.append((tiempos[i] + tiempos[i + delta_t]) / 2)

    # Filtrar temperatura en los mismos puntos
    temperaturas_filtradas = np.interp(tiempos_prom, tiempos, temperaturas)

    # Graficar
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=tiempos_prom, y=cuentas_tasa, mode='lines+markers', name="COUNT/delta_t", line=dict(color="green")
    ))
    
    fig.add_trace(go.Scatter(
        x=tiempos_prom, y=temperaturas_filtradas, mode='lines+markers', name="Temperatura (°C)", 
        line=dict(color="orange"), yaxis="y2"
    ))
    
    fig.update_layout(
        title="COUNT/delta_t y Temperatura vs Tiempo",
        xaxis=dict(title="Tiempo (s)"),
        yaxis=dict(
            title="COUNT/delta_t",
            tickfont=dict(color="green")
        ),
        yaxis2=dict(
            title="Temperatura (°C)",
            tickfont=dict(color="orange"),
            overlaying="y",
            side="right"
        ),
        # legend=dict(x=0.05, y=0.95),
        template="plotly_white"
    )
    
    fig.show()


# def graficar_metodo_5_media_movil(tiempos, cuentas, temperaturas, delta_t, ventana):
#     import plotly.graph_objects as go
#     import numpy as np
    
#     cuentas_tasa = []
#     tiempos_prom = []
#     i = 0
#     while i < len(tiempos) - 1:
#         t1 = tiempos[i]
#         ind_t2 = i
#         while ind_t2 < len(tiempos) and tiempos[ind_t2] - t1 < delta_t:
#             ind_t2 += 1
        
#         if ind_t2 < len(tiempos):
#             t2 = tiempos[ind_t2]
#             impactos_intervalo = cuentas[ind_t2] - cuentas[i]
#             tasa_impactos = impactos_intervalo / (t2 - t1)
#             cuentas_tasa.append(tasa_impactos)
#             tiempos_prom.append((t1 + t2) / 2)
        
#         i = ind_t2
    
#     temperaturas_filtradas = np.interp(tiempos_prom, tiempos, temperaturas)
    
#     def media_movil(arr, ventana):
#         return np.convolve(arr, np.ones(ventana)/ventana, mode='valid')
    
#     cuentas_tasa_suavizada = media_movil(cuentas_tasa, ventana)
#     tiempos_suavizados = tiempos_prom[:len(cuentas_tasa_suavizada)]
    
#     fig = go.Figure()
    
#     fig.add_trace(go.Scatter(
#         x=tiempos_suavizados, y=cuentas_tasa_suavizada, mode='lines', name="COUNT/delta_t (Media Móvil)", line=dict(color="green")
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=tiempos_prom, y=temperaturas_filtradas, mode='lines+markers', name="Temperatura (°C)", line=dict(color="orange"), yaxis="y2"
#     ))
    
#     fig.update_layout(
#         title="COUNT/delta_t (Media Móvil) y Temperatura vs Tiempo",
#         xaxis=dict(title="Tiempo (s)"),
#         yaxis=dict(
#             title="COUNT/delta_t (Media Móvil)",
#             tickfont=dict(color="green")
#         ),
#         yaxis2=dict(
#             title="Temperatura (°C)",
#             tickfont=dict(color="orange"),
#             overlaying="y",
#             side="right"
#         ),
#         legend=dict(x=0.05, y=0.95),
#         template="plotly_white"
#     )
    
#     fig.show()


def graficar_metodo_5(tiempos, cuentas, temperaturas, interrupciones, delta_t, info):
    # Calcular la cantidad de impactos en cada intervalo de tiempo
    impactos = np.diff(cuentas, prepend=cuentas[0])
    impactos[impactos < 0] = 0  # Asegurar que solo cuente aumentos

    # Calcular COUNT/delta_t
    cuentas_tasa = []
    tiempos_prom = []
    i = 0
    while i < len(tiempos) - 1:
        t1 = tiempos[i]
        ind_t2 = i
        while ind_t2 < len(tiempos) and tiempos[ind_t2] - t1 < delta_t:
            ind_t2 += 1
        
        if ind_t2 < len(tiempos):
            t2 = tiempos[ind_t2]
            impactos_intervalo = cuentas[ind_t2] - cuentas[i]
            tasa_impactos = impactos_intervalo / (t2 - t1)
            cuentas_tasa.append(tasa_impactos)
            tiempos_prom.append((t1 + t2) / 2)
        
        i = ind_t2

    # Filtrar temperatura en los mismos puntos
    temperaturas_filtradas = np.interp(tiempos_prom, tiempos, temperaturas)

    # cuentas_tasa = sliding_moving_average(cuentas_tasa, len(cuentas_tasa), )

    # for i in range(1, len(cuentas_tasa)):
    #     if cuentas_tasa[i] < 0.1: # sin cuentas por error del sistema
    #         cuentas_tasa[i] = (cuentas_tasa[i-1] + cuentas_tasa[i+1] ) / 2
    # cuentas_tasa = sliding_moving_average(cuentas_tasa, len(cuentas_tasa), 3)

    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=tiempos_prom, y=cuentas_tasa, mode='lines+markers', name="COUNT/delta_t", line=dict(color="green")
    ))
    
    fig.add_trace(go.Scatter(
        x=tiempos_prom, y=temperaturas_filtradas, mode='lines+markers', name="Temperatura (°C)", line=dict(color="orange"), yaxis="y2"
    ))

    for i, (inicio, fin) in enumerate(interrupciones):
        if i == 0:
            fig.add_trace(go.Scatter(
                x=[inicio, inicio], y=[min(cuentas_tasa), max(cuentas_tasa)],
                mode="lines", line=dict(color="red", dash="dot"),
                name="Inicio de interrupción"
            ))

            fig.add_trace(go.Scatter(
                x=[fin, fin], y=[min(cuentas_tasa), max(cuentas_tasa)],
                mode="lines", line=dict(color="blue", dash="dot"),
                name="Fin de interrupción"
            ))
        else: 
            fig.add_trace(go.Scatter(
                x=[inicio, inicio], y=[min(cuentas_tasa), max(cuentas_tasa)],
                mode="lines", line=dict(color="red", dash="dot"),
                showlegend=False
            ))

            # Línea de fin (azul)
            fig.add_trace(go.Scatter(
                x=[fin, fin], y=[min(cuentas_tasa), max(cuentas_tasa)],
                mode="lines", line=dict(color="blue", dash="dot"),
                showlegend=False
            ))
    
    fig.update_layout(
        title=info,
        xaxis=dict(title="Tiempo (s)"),
        yaxis=dict(
            title="COUNT/delta_t",
            tickfont=dict(color="green")
        ),
        yaxis2=dict(
            title="Temperatura (°C)",
            tickfont=dict(color="orange"),
            overlaying="y",
            side="right"
        ),
        # legend=dict(x=0.05, y=0.95),
        template="plotly_white"
    )
    
    fig.show()

# def graficar_burbujas(tiempos, cuentas, temperaturas, delta_t, info):
#     """Grafica un diagrama de burbujas de COUNT/delta_t vs. Temperatura con el eje de tiempo."""
#     tiempos_prom, cuentas_tasa, temperaturas_filtradas = calcular_tasa_y_temperatura(tiempos, cuentas, temperaturas, delta_t)
    
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=temperaturas_filtradas, 
#         y=cuentas_tasa, 
#         mode='markers', 
#         marker=dict(size=np.array(tiempos_prom) / max(tiempos_prom) * 20, color=tiempos_prom, colorscale='Viridis', showscale=True),
#         name='COUNT/delta_t'
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=tiempos_prom,
#         y=cuentas_tasa,
#         mode='lines+markers',
#         name='COUNT/delta_t vs Tiempo',
#         line=dict(color='green')
#     ))
    
#     fig.update_layout(
#         title=info,
#         xaxis=dict(title='Temperatura (°C)'),
#         yaxis=dict(title='COUNT/delta_t'),
#         xaxis2=dict(title='Tiempo (s)', overlaying='x', side='top'),
#         template='plotly_white'
#     )
    
#     fig.show()

def graficar_burbujas(tiempos, cuentas, temperaturas, delta_t, info):
    """Grafica un diagrama de burbujas de COUNT/delta_t vs. Temperatura con el eje de tiempo."""
    tiempos_prom, cuentas_tasa, temperaturas_filtradas = calcular_tasa_y_temperatura(tiempos, cuentas, temperaturas, delta_t)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tiempos_prom, 
        y=cuentas_tasa, 
        mode='markers', 
        marker=dict(size=np.array(temperaturas_filtradas) / max(temperaturas_filtradas) * 20, color=temperaturas_filtradas, colorscale='Viridis', showscale=True),
        name='COUNT/delta_t'
    ))
    
    fig.update_layout(
        title=info,
        xaxis=dict(title='Tiempo (s)'),
        yaxis=dict(title='COUNT/delta_t'),
        xaxis2=dict(title='Temperatura (°C)', overlaying='x', side='top'),
        template='plotly_white'
    )
    
    fig.show()

def graficar_lineas_suavizadas(tiempos, cuentas, temperaturas, interrupciones, delta_t, info):
    """Grafica COUNT/delta_t y Temperatura con una curva suavizada usando LOESS."""
    tiempos_prom, cuentas_tasa, temperaturas_filtradas = calcular_tasa_y_temperatura(tiempos, cuentas, temperaturas, delta_t)
    # cuentas_tasa = sliding_moving_average(cuentas_tasa, len(cuentas_tasa), 9)
    # print(cuentas_tasa)
    # for i in range(len(cuentas_tasa)):
    #     if cuentas_tasa[i] < 5:
    #         cuentas_tasa[i] = (cuentas_tasa[i-1] + cuentas_tasa[i+1] ) / 2

    # Suavizado con UnivariateSpline
    spline_tasa = UnivariateSpline(tiempos_prom, cuentas_tasa, s=len(tiempos_prom)*0.05)
    spline_temp = UnivariateSpline(tiempos_prom, temperaturas_filtradas, s=len(tiempos_prom)*0.05)
    tiempos_suavizados = np.linspace(min(tiempos_prom), max(tiempos_prom), 200)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tiempos_suavizados, 
        y=spline_tasa(tiempos_suavizados),
        mode='lines',
        name='COUNT/delta_t (suavizado)',
        line=dict(color='green')
    ))
    
    fig.add_trace(go.Scatter(
        x=tiempos_suavizados, 
        y=spline_temp(tiempos_suavizados),
        mode='lines',
        name='Temperatura (°C) (suavizado)',
        line=dict(color='orange'),
        yaxis='y2'
    ))

    for i, (inicio, fin) in enumerate(interrupciones):
        if i == 0:
            fig.add_trace(go.Scatter(
                x=[inicio, inicio], y=[min(cuentas_tasa), max(cuentas_tasa)*1.2],
                mode="lines", line=dict(color="red", dash="dot"),
                name="Inicio de interrupción"
            ))

            fig.add_trace(go.Scatter(
                x=[fin, fin], y=[min(cuentas_tasa), max(cuentas_tasa)*1.2],
                mode="lines", line=dict(color="blue", dash="dot"),
                name="Fin de interrupción"
            ))
        else: 
            fig.add_trace(go.Scatter(
                x=[inicio, inicio], y=[min(cuentas_tasa), max(cuentas_tasa)*1.2],
                mode="lines", line=dict(color="red", dash="dot"),
                showlegend=False
            ))

            # Línea de fin (azul)
            fig.add_trace(go.Scatter(
                x=[fin, fin], y=[min(cuentas_tasa), max(cuentas_tasa)*1.2],
                mode="lines", line=dict(color="blue", dash="dot"),
                showlegend=False
            ))
    
    fig.update_layout(
        title=info,
        xaxis=dict(title='Tiempo (s)'),
        yaxis=dict(title='COUNT/delta_t', tickfont=dict(color='green'), range=[min(cuentas_tasa) * 0.9, max(cuentas_tasa) * 1.1]),
        yaxis2=dict(title='Temperatura (°C)', tickfont=dict(color='orange'), overlaying='y', side='right'),
        template='plotly_white'
    )
    
    fig.show()

def graficar_histogramas(tiempos, cuentas, temperaturas, delta_t, info):
    """Grafica histogramas de COUNT/delta_t y Temperatura a lo largo del tiempo."""
    tiempos_prom, cuentas_tasa, temperaturas_filtradas = calcular_tasa_y_temperatura(tiempos, cuentas, temperaturas, delta_t)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=tiempos_prom, 
        y=cuentas_tasa, 
        name='COUNT/delta_t',
        marker_color='green',
        opacity=0.7
    ))
    
    fig.add_trace(go.Bar(
        x=tiempos_prom, 
        y=temperaturas_filtradas, 
        name='Temperatura (°C)',
        marker_color='orange',
        opacity=0.7,
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=info,
        xaxis=dict(title='Tiempo (s)'),
        yaxis=dict(title='COUNT/delta_t', tickfont=dict(color='green')),
        yaxis2=dict(title='Temperatura (°C)', tickfont=dict(color='orange'), overlaying='y', side='right'),
        barmode='overlay',
        template='plotly_white'
    )
    
    fig.show()


def graficar_3d(tiempos, cuentas, temperaturas, delta_t, info):
    """Grafica los datos en 3D con tiempo, COUNT/delta_t y temperatura."""
    tiempos_prom, cuentas_tasa, temperaturas_filtradas = calcular_tasa_y_temperatura(tiempos, cuentas, temperaturas, delta_t)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=tiempos_prom,
        y=cuentas_tasa,
        z=temperaturas_filtradas,
        mode='markers',
        marker=dict(size=5, color=temperaturas_filtradas, colorscale='Viridis', showscale=True),
        name='Datos 3D'
    ))
    
    fig.update_layout(
        title=info,
        scene=dict(
            xaxis_title='Tiempo (s)',
            yaxis_title='COUNT/delta_t',
            zaxis_title='Temperatura (°C)'
        ),
        template='plotly_white'
    )
    
    fig.show()


# def graficar_3d(tiempos, cuentas, temperaturas, delta_t, info):
#     """Grafica los datos en 3D como una superficie con tiempo, COUNT/delta_t y temperatura."""
#     tiempos_prom, cuentas_tasa, temperaturas_filtradas = calcular_tasa_y_temperatura(tiempos, cuentas, temperaturas, delta_t)
    
#     # Crear una malla 2D
#     xi = np.linspace(min(tiempos_prom), max(tiempos_prom), 50)
#     yi = np.linspace(min(cuentas_tasa), max(cuentas_tasa), 50)
#     X, Y = np.meshgrid(xi, yi)
#     Z = griddata((tiempos_prom, cuentas_tasa), temperaturas_filtradas, (X, Y), method='cubic')
    
#     fig = go.Figure()
#     fig.add_trace(go.Surface(x=X, y=Y, z=Z, colorscale='Viridis'))
    
#     fig.update_layout(
#         title=info,
#         scene=dict(
#             xaxis_title='Tiempo (s)',
#             yaxis_title='COUNT/delta_t',
#             zaxis_title='Temperatura (°C)'
#         ),
#         template='plotly_white'
#     )
    
#     fig.show()

def sliding_moving_average(input, N, M):
    output = np.zeros(N)
    accumulator = 0.0
    aux = int((M - 1) / 2)

    # Para las primeras aux+1 muestras
    for i in range(M):
        accumulator += input[i]
        if i >= aux:
            output[i - aux] = accumulator / (i + 1)

    # Para el resto de las muestras (ventanas deslizantes completas)
    for i in range(M - aux, N - aux):
        accumulator += input[i + aux] - input[i - aux - 1]  # Actualiza el acumulador
        output[i] = accumulator / M  # Calcula el promedio

    # Para los últimos valores
    for i in range(N - aux, N):
        accumulator -= input[i - aux - 1]  # Restar el valor sobrante
        output[i] = accumulator / (N - i + aux)  # Promedio con los valores restantes

    return output



if __name__ == "__main__":
    First_VCurrent = 1.2160509

    # delta_t = 30
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\src\pruebas_24_03_25.txt"
    # archivo = "pruebas_24_03_25.txt"
    # inicio_linea = 43
    # fin_linea = 668
    # moneda = "NONE"
    # fecha = "24/03/25"
    # compensacion = "sin"
    # OV = 2 ########## PLOTS GUARDADOS

    # delta_t = 10
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\src\pruebas_24_03_25.txt"
    # archivo = "pruebas_24_03_25.txt"
    # # inicio_linea = 721
    # # fin_linea = 1858
    # # # fin_linea = 1915 # plots guardados
    # inicio_linea = 1986
    # fin_linea = 
    # moneda = "CS-137"
    # fecha = "24/03/25"
    # compensacion = "sin"
    # OV = 1.5                      ############ plots guardados 

    # delta_t = 60
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\src\pruebas_24_03_25.txt"
    # archivo = "pruebas_24_03_25.txt"
    # inicio_linea = 1986
    # fin_linea = 16011
    # # inicio_linea = 2803 ###########  plots guardados
    # # fin_linea = 11649
    # # inicio_linea = 10789
    # # fin_linea = 13401
    # moneda = "CS-137"
    # fecha = "24/03/25"
    # compensacion = "con"
    # OV = 1.5

    # delta_t = 10
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\logs\device-monitor-250325-182158.log"
    # archivo = "device-monitor-250325-182158.log"
    # inicio_linea = 87
    # fin_linea = 3105
    # moneda = "Co-60"
    # fecha = "25/03/25"
    # compensacion = "sin"
    # OV = 1.5      ########### PLOTS GUARDADOS

    # delta_t = 10
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\logs\device-monitor-250325-184825.log"
    # archivo = "device-monitor-250325-184825.log"
    # # inicio_linea = 897
    # inicio_linea = 1051
    # fin_linea = 4781
    # moneda = "Co-60"
    # fecha = "25/03/25"
    # compensacion = "con"
    # OV = 1.5      ########### PLOTS GUARDADOS

    # delta_t = 60
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\logs\device-monitor-250325-192616.log"
    # archivo = "device-monitor-250325-192616.log"
    # inicio_linea = 896
    # fin_linea = 12070
    # moneda = "CS-137"
    # fecha = "25/03/25"
    # compensacion = "sin"
    # OV = 1.5      ########### PLOTS GUARDADOS

    # delta_t = 60
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\logs\device-monitor-250325-194843.log"
    # archivo = "device-monitor-250325-194843.log"
    # inicio_linea = 893
    # fin_linea = 26849
    # moneda = "CS-137"
    # fecha = "25/03/25"
    # compensacion = "sin"
    # OV = 1.5      ########### PLOTS GUARDADOS

    # delta_t = 10
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\logs\device-monitor-250325-204629.log"
    # archivo = "device-monitor-250325-204629.log"
    # inicio_linea = 1711
    # fin_linea = 2701
    # moneda = "CS-137"
    # fecha = "25/03/25"
    # compensacion = "con"
    # OV = 1.5        ########### PLOTS GUARDADOS COUNT1 y COUNT2

    # delta_t = 10
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\logs\device-monitor-250325-205139.log"
    # archivo = "device-monitor-250325-205139.log"
    # inicio_linea = 1711
    # fin_linea = 4377
    # moneda = "CS-137"
    # fecha = "25/03/25"
    # compensacion = "con"
    # OV = 1.5 ########### PLOTS GUARDADOS COUNT1 y COUNT2

    delta_t = 10
    archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\logs\device-monitor-250325-211210.log"
    archivo = "device-monitor-250325-211210.log"
    inicio_linea = 1711
    fin_linea = 3361
    moneda = "CS-137"
    fecha = "25/03/25"
    compensacion = "con"
    OV = 1.5        ########### PLOTS GUARDADOS COUNT1 y COUNT2

    # delta_t = 120
    # archivo_txt = r"C:\Users\Pc\Documents\Platform_Projects\MUA_Control_Placa_Pruebas\logs\device-monitor-250515-195616.log"
    # archivo = "device-monitor-250515-195616.log"
    # inicio_linea = 875
    # fin_linea = 51805
    # moneda = "CS-137"
    # fecha = "15/05/25"
    # compensacion = "con"
    # OV = 5.5


    info = f"Prueba de flujo de partículas: Fecha {fecha}, Fuente {moneda}, {compensacion} compensación, " + \
            f"OverVoltage = {OV:.1f} V, archivo {archivo}, delta_t = {delta_t} seg."

    tiempos, cuentas, temperaturas, interrupciones = procesar_datos(archivo_txt, inicio_linea, fin_linea)
    """
    Cambiar en procesar_datos() COUNT1 o COUNT2 segun el canal que se quiera leer (ultimos logs solamente)
    """

    # print("Tiempos:", tiempos)
    # print("Cuentas:", cuentas)
    # print("Temperaturas:", temperaturas)
    # print("Interrupciones: ", interrupciones)
    
    graficar_metodo_1(tiempos, cuentas, temperaturas, interrupciones, info) ##
    # graficar_metodo_2(cuentas, temperaturas)
    # graficar_metodo_3(tiempos, cuentas, temperaturas)
    # graficar_metodo_4(tiempos, cuentas, temperaturas, delta_t)
    graficar_metodo_5(tiempos, cuentas, temperaturas, interrupciones, delta_t, info) ##
    # graficar_burbujas(tiempos, cuentas, temperaturas, delta_t, info)
    graficar_lineas_suavizadas(tiempos, cuentas, temperaturas, interrupciones, delta_t, info) ##
    # graficar_histogramas(tiempos, cuentas, temperaturas, delta_t, info)
    # graficar_3d(tiempos, cuentas, temperaturas, delta_t, info)
