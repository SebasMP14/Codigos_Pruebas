import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Aquí debes agregar tus datos de tiempo (horas y minutos) y el conteo de partículas
horas_minutos = ["13:25:31", "13:27:18", "13:29:05", "13:30:52", "13:32:39"]  # Ejemplo
conteo_particulas = [40, 30, 41, 29, 30]  # Ejemplo

# Convertir horas y minutos a objetos datetime
tiempos = [datetime.strptime(hm, "%H:%M") for hm in horas_minutos]

# Crear la gráfica
plt.figure(figsize=(10, 5))
plt.plot(tiempos, conteo_particulas, marker="o", linestyle="-", color="b", label="Conteo de partículas")

# Formatear eje X para que muestre las horas y minutos correctamente
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=1))  # Ajusta el intervalo de etiquetas según los datos

# Etiquetas y título
plt.xlabel("Hora")
plt.ylabel("Conteo de Partículas")
plt.title("Conteo de Partículas por Minuto")
plt.grid(True)
plt.legend()
plt.xticks(rotation=45)  # Rotar etiquetas del eje X para mejor visibilidad

# Mostrar la gráfica
plt.show()
