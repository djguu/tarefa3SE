import csv, math, haversine, xlsxwriter

data = []
line_count = 0


def getCsvData(file, fields):
    with open(file, mode='r') as csv_file:
        global line_count
        csv_reader = csv.DictReader(csv_file,
                                    fieldnames=fields)
        line_count = 0
        for row in csv_reader:
            if line_count >= 6:
                # print(
                #     f'\t{row["Latitude"]}\t{row["Longitude"]}\t{row["N"]}\t{row["Altitude"]}\t{row["Date_nDays"]}\t{row["Date"]}\t{row["Time"]}')
                data.append(row)
            line_count += 1
        print(f'Processed {line_count} lines.')
        return csv_reader


def csvToXls(csvDict):
    workbook = xlsxwriter.Workbook('data.xlsx')
    worksheet = workbook.add_worksheet('Dados')

    worksheet.set_column('A:H', 20)

    bold = workbook.add_format({'bold': True})

    row = 0
    col = 0

    for key in csvDict.fieldnames:
        worksheet.write(row, col, key, bold)
        col += 1

    row = 2

    for value in data:
        col = 0
        for key in csvDict.fieldnames:
            worksheet.write(row, col, value[key])
            col += 1
        # worksheet.write(row, 0, value["Latitude"])
        # worksheet.write(row, 1, value["Longitude"])
        # worksheet.write(row, 2, value["N"])
        # worksheet.write(row, 3, value["Altitude"])
        # worksheet.write(row, 4, value["Date_nDays"])
        # worksheet.write(row, 5, value["Date"])
        # worksheet.write(row, 6, value["Time"])
        row += 1

    workbook.close()


def main():
    data = getCsvData('20081026094426.csv', ["Latitude", "Longitude", "N", "Altitude", "Date_nDays", "Date", "Time"])
    csvToXls(data)


main()
