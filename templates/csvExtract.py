import os
import csv
import re
import xlsxwriter
from flask import Blueprint, jsonify, request
from haversine import haversine, Unit
from pathlib import Path
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

api = Blueprint('api', __name__, template_folder='templates')

data = []
line_count = 0
total_distance = 0.0
total_time = 0.0

UPLOAD_FOLDER = 'downloads'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx', 'xls'}


@api.route("/csv", methods=['GET','POST'])
def main():
    global data
    data = []
    if request.method == 'POST':
        filename, file_path, fields, start_data, fields_valid = getParams()
        xls = filename + '.xlsx'

        if fields_valid:
            dados = getCsvData(file_path, fields, start_data)
            dataProcess()
            csvToXls(dados, xls)
            if len(data) > 0:
                return jsonify(
                    {'ok': True, 'data': data, "count": len(data), "total distance": total_distance,
                     "total time": total_time}), 200
            else:
                return jsonify({'ok': False, 'message': 'No points found'}), 400
        else:
            return 'Error with a field'

    return '''
    <html>
   <body>
      <form action = "" method = "POST" 
         enctype = "multipart/form-data">
         Ficheiro:
         <input type = "file" name = "file" /><br/>
         Parametros: 
         <input type = "text" name = "fields"  size="150"/><br/>
         Linha em que inicia os dados: 
         <input type = "number" name = "start_data" /><br/>
         <input type = "submit"/>
      </form>
   </body>
</html>
    '''


def getParams():
    fields_valid = False
    path = ''
    full_path = ''
    filename = ''
    if 'file' not in request.files:
        file = None
    else:
        file = request.files['file']
        path = Path(__file__).parent.parent.joinpath(UPLOAD_FOLDER)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=False)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        full_path = os.path.join(path, filename)
        file.save(full_path)

    start_data = request.form.get('start_data', None)
    if start_data == '':
        start_data = None
    elif start_data is not None:
        start_data = int(start_data)

    if file is not None and start_data is not None:
        fields_valid = True

    # get fields from request
    get_fields = request.form.get('fields')

    fields = fieldsToArray(get_fields)

    return filename, full_path, fields, start_data, fields_valid


def getCsvData(file, fields, start_data):
    with open(file, mode='r') as csv_file:
        global line_count, data
        csv_reader = csv.DictReader(csv_file, fieldnames=fields)

        line_count = 0
        for row in csv_reader:
            if line_count >= start_data - 1:
                data.append(row)
            line_count += 1
        return csv_reader


def dataProcess():
    global data, total_distance, total_time
    pos = 0
    distancia = 0.0

    for row in data:
        if row['altitude'] is not None:
            if float(row["altitude"]) <= 0:
                row['altitude'] = -777

        if row["tempo (s)"] is None and row['data'] is not None and row['hora'] is not None:
            if pos - 1 >= 0:
                last_row = data[pos - 1]

                pos1 = datetime.strptime(row["data"] + ' ' + row["hora"], '%Y-%m-%d %H:%M:%S')
                pos2 = datetime.strptime(last_row["data"] + ' ' + last_row["hora"], '%Y-%m-%d %H:%M:%S')

                row["tempo (s)"] = timeCalc(pos2, pos1)

                total_time += row["tempo (s)"]
            else:
                row["tempo (s)"] = 0

        if row["distancia (m)"] is None:
            if pos - 1 >= 0:
                last_row = data[pos - 1]

                pos1 = (float(row["latitude"]), float(row["longitude"]))
                pos2 = (float(last_row["latitude"]), float(last_row["longitude"]))

                row["distancia (m)"] = distancia = distanceCalc(pos1, pos2)

                total_distance += row["distancia (m)"]
            else:
                row["distancia (m)"] = 0

        if row["vel. deslocação m/s"] is None and row["tempo (s)"] is not None:
            try:
                row["vel. deslocação m/s"] = round(distancia / float(row["tempo (s)"]), 3)
                row["vel. deslocação km/h"] = round(float(row["vel. deslocação m/s"]) * 3.6, 3)
            except ZeroDivisionError:
                row["vel. deslocação m/s"] = 0.0
                row["vel. deslocação km/h"] = 0.0

        if row["meio transporte"] is None and row["vel. deslocação m/s"] is not None:
            vel = row["vel. deslocação m/s"]

            if vel == 0.0:
                row["meio transporte"] = 'Parado'
            elif 0.0 < vel <= 2.6:
                row["meio transporte"] = 'Andar'
            elif 2.6 < vel <= 3.6:
                row["meio transporte"] = 'Correr'
            elif 3.6 < vel <= 13:
                row["meio transporte"] = 'Bicicleta'
            elif 13 < vel <= 55:
                row["meio transporte"] = 'Carro'
            elif 55 < vel <= 100:
                row["meio transporte"] = 'Comboio'
            else:
                row["meio transporte"] = 'nd'

        pos += 1


def csvToXls(csv_dict, xls):
    global total_time, total_distance

    name_xls = Path(__file__).parent.parent.joinpath('xls')

    if not name_xls.exists():
        name_xls.mkdir(parents=True, exist_ok=False)

    workbook = xlsxwriter.Workbook(name_xls.joinpath(xls))
    worksheet = workbook.add_worksheet('Dados')

    worksheet.set_column('A:L', 20)

    bold = workbook.add_format({'bold': True})

    worksheet.write(1, 0, 'Total distance(mt):', bold)
    worksheet.write(1, 1, total_distance)
    worksheet.write(1, 3, 'Total time:', bold)
    worksheet.write(1, 4, str(timedelta(seconds=total_time)))

    row = 3
    col = 0

    for key in csv_dict.fieldnames:
        worksheet.write(row, col, key, bold)
        col += 1

    row = 5

    for value in data:
        col = 0
        for key in csv_dict.fieldnames:
            worksheet.write(row, col, value[key])
            col += 1
        row += 1

    workbook.close()


def distanceCalc(pos1, pos2):
    return round(haversine(pos1, pos2, unit=Unit.METERS), 3)


def timeCalc(time1, time2):
    return (time2 - time1).total_seconds()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def fieldsToArray(fields):
    parts = re.split(r"""("[^"]*"|'[^']*')""", fields)
    parts[::2] = map(lambda s: "".join(s.split()), parts[::2])  # removes possible spaces outside quotes
    str1 = ("".join(parts))
    str2 = str1.replace(']', '').replace('[', '')  # remove square brackets in case there are
    str3 = str2.replace('"', '').replace("'", "")  # remove quotes in case there are
    fields = str3.split(",")  # splits into array
    fields = [x.lower() for x in fields]

    if 'altitude' not in fields:
        fields.append('altitude')

    if 'tempo (s)' not in fields:
        fields.append('tempo (s)')

    if 'distancia (m)' not in fields:
        fields.append('distancia (m)')

    if 'vel. deslocação m/s' not in fields:
        fields.append('vel. deslocação m/s')

    if 'meio transporte' not in fields:
        fields.append('meio transporte')

    if 'data' not in fields:
        fields.append('data')

    if 'hora' not in fields:
        fields.append('hora')

    return fields
