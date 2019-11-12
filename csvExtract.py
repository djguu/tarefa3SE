import csv
import xlsxwriter
from haversine import haversine, Unit
from pathlib import Path
from datetime import datetime, timedelta

data = []
line_count = 0
total_distance = 0.0
total_time = 0.0



def getCsvData(file, fields):
    path = Path(__file__).parent.joinpath(file)

    with open(path, mode='r') as csv_file:
        global line_count, data
        csv_reader = csv.DictReader(csv_file, fieldnames=fields)
        line_count = 0
        for row in csv_reader:
            if line_count >= 6:
                data.append(row)
            line_count += 1
        return csv_reader


def distanceCalc(pos1, pos2):
    return round(haversine(pos1, pos2, unit=Unit.METERS), 3)


def timeCalc(time1, time2):
    return (time2 - time1).total_seconds()


def dataProcess():
    global data, total_distance, total_time
    pos = 0
    last_row = None
    next_row = None
    distancia = 0.0

    for row in data:
        if row["Tempo (s)"] is None:
            if pos - 1 >= 0:
                last_row = data[pos - 1]

                pos1 = datetime.strptime(row["Data"] + ' ' + row["Hora"], '%Y-%m-%d %H:%M:%S')
                pos2 = datetime.strptime(last_row["Data"] + ' ' + last_row["Hora"], '%Y-%m-%d %H:%M:%S')

                row["Tempo (s)"] = timeCalc(pos2, pos1)

                total_time += row["Tempo (s)"]
            else:
                row["Tempo (s)"] = 0

        if row["Distancia (m)"] is None:
            if pos - 1 >= 0:
                last_row = data[pos - 1]

                pos1 = (float(row["Latitude"]), float(row["Longitude"]))
                pos2 = (float(last_row["Latitude"]), float(last_row["Longitude"]))

                row["Distancia (m)"] = distancia = distanceCalc(pos1, pos2)

                total_distance += row["Distancia (m)"]
            else:
                row["Distancia (m)"] = 0

        if row["Vel. deslocação m/s"] is None:
            try:
                row["Vel. deslocação m/s"] = round(distancia / float(row["Tempo (s)"]), 3)
                row["Vel. deslocação km/h"] = round(float(row["Vel. deslocação m/s"]) * 3.6, 3)
            except:
                row["Vel. deslocação m/s"] = 0.0
                row["Vel. deslocação km/h"] = 0.0

        if row["Meio Transporte"] is None:
            vel = row["Vel. deslocação m/s"]

            if(vel == 0.0):
                row["Meio Transporte"] = 'Parado'
            elif 0.0 < vel <= 2.6:
                row["Meio Transporte"] = 'Andar'
            elif 2.6 < vel <= 3.6:
                row["Meio Transporte"] = 'Correr'
            elif 3.6 < vel <= 13:
                row["Meio Transporte"] = 'Bicicleta'
            elif 13 < vel <= 55:
                row["Meio Transporte"] = 'Carro'
            elif 55 < vel <= 100:
                row["Meio Transporte"] = 'Comboio'
            else:
                row["Meio Transporte"] = 'nd'

        pos += 1


def csvToXls(csvDict):
    global total_time, total_distance
    workbook = xlsxwriter.Workbook('data.xlsx')
    worksheet = workbook.add_worksheet('Dados')

    worksheet.set_column('A:L', 20)

    bold = workbook.add_format({'bold': True})

    worksheet.write(1, 0, 'Total distance(mt):', bold)
    worksheet.write(1, 1, total_distance)
    worksheet.write(1, 3, 'Total time:', bold)
    worksheet.write(1, 4, str(timedelta(seconds=total_time)))

    row = 3
    col = 0

    for key in csvDict.fieldnames:
        worksheet.write(row, col, key, bold)
        col += 1

    row = 5

    for value in data:
        col = 0
        for key in csvDict.fieldnames:
            worksheet.write(row, col, value[key])
            col += 1
        row += 1

    workbook.close()


def main():
    global data
    file = '20081026094426.csv'
    fields = ["Latitude", "Longitude", "N", "Altitude", "Date_nDays", "Data", "Hora", "Distancia (m)", "Tempo (s)", "Vel. deslocação m/s", "Vel. deslocação km/h", "Meio Transporte"]
    dados = getCsvData(file, fields)
    dataProcess()
    csvToXls(dados)


main()
