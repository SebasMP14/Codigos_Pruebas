# -*- coding: utf-8 -*-
"""
Created on Sun Jun 23 16:15:35 2024

@author: Pc
"""

import csv
import struct
import gzip
import time
from datetime import datetime, timedelta
import random
import os
import h5py
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd



# Configuración del número de registros y intervalo de tiempo (en minutos)
num_records = 60 * 1 * 12 # 1.5 hs de datos, un registro por minuto

# Función para generar datos sintéticos
def generate_synthetic_data(num_records):
    data = []
    start_time = datetime.now()
    for i in range(num_records):
        timestamp = start_time + timedelta(minutes=i)
        temperature = round(random.uniform(15.0, 35.0), 2)
        voltage = round(random.uniform(3.0, 5.0), 2)
        conteo1 = random.randint(0, 100)
        conteo2 = random.randint(0, 100)
        latx = round(random.uniform(-90.0, 90.0), 6)
        laty = round(random.uniform(-180.0, 180.0), 6)
        data.append([timestamp, temperature, voltage, conteo1, conteo2, latx, laty])
    return data

# Generar datos sintéticos
data = generate_synthetic_data(num_records) # Un registro por minuto de 7 elementos

# Guardar datos en formato CSV
def save_as_csv(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'temperature', 'voltage', 'conteo1', 'conteo2', 'latx', 'laty'])
        for row in data:
            writer.writerow(row)

# Guardar datos en formato binario
def save_as_binary(filename, data):
    with open(filename, 'wb') as binfile:
        for row in data:
            timestamp = time.mktime(row[0].timetuple())
            #binfile.write(struct.pack('d', timestamp))
            binfile.write(struct.pack('dffiidd', timestamp, row[1], row[2], row[3], row[4], row[5], row[6]))

# Guardar datos en formato binario comprimido
def save_as_compressed(filename, data):
    with gzip.open(filename, 'wb') as gzfile:
        for row in data:
            timestamp = time.mktime(row[0].timetuple())
            #gzfile.write(struct.pack('d', timestamp))
            gzfile.write(struct.pack('dffiidd', timestamp, row[1], row[2], row[3], row[4], row[5], row[6]))

def save_as_hdf5(filename, data):
    with h5py.File(filename, 'w') as hdf5file:
        dt = h5py.special_dtype(vlen=str)
        dset = hdf5file.create_dataset("data", (len(data), 7), dtype=dt)
        for i, row in enumerate(data):
            timestamp = time.mktime(row[0].timetuple())
            dset[i] = [str(timestamp), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6])]

def save_as_parquet(filename, data):
    df = pd.DataFrame(data, columns=['timestamp', 'temperature', 'voltage', 'conteo1', 'conteo2', 'latx', 'laty'])
    df['timestamp'] = df['timestamp'].apply(lambda x: time.mktime(x.timetuple()))
    table = pa.Table.from_pandas(df)
    pq.write_table(table, filename)


# Guardar archivos
save_as_csv('data.csv', data)
save_as_binary('data.bin', data)
save_as_compressed('data.gz', data)
save_as_hdf5('data.h5', data)
save_as_parquet('data.parquet', data)

# Comparar tamaños de los archivos
csv_size = os.path.getsize('data.csv')
bin_size = os.path.getsize('data.bin')
gz_size = os.path.getsize('data.gz')
h5_size = os.path.getsize('data.h5')
parquet_size = os.path.getsize('data.parquet')

print(f"Tamaño del archivo CSV: {csv_size} bytes")
print(f"Tamaño del archivo binario: {bin_size} bytes")
print(f"Tamaño del archivo comprimido: {gz_size} bytes")
print(f"Tamaño del archivo HDF5: {h5_size} bytes")
print(f"Tamaño del archivo Parquet: {parquet_size} bytes")