from . import os
from . import csv
from .table_utils import GetTableColumn

def downloadCSV(Table, tableRecords, filename, col_exclude, folder = 'static/csv-download'):

    root_path = os.path.dirname(os.path.dirname(__file__))
    csv_path = os.path.join(root_path, folder, filename)
    outfile = open(csv_path, 'w+')
    outcsv = csv.writer(outfile)

    columns = GetTableColumn(Table, col_exclude).values()
    outfile.write(','.join(columns) + "\n")

    for record in tableRecords:
        outfile.write(','.join(getRowCSV(Table, record, col_exclude)) + '\n')

    outfile.close()
    return csv_path    

    
def getRowCSV(Table, record, col_exclude):
    rowCSV = []
    for item in Table.__table__.columns:
        if str(item.name) not in col_exclude:
            if getattr(record, str(item.name)) == None:
                rowCSV.append(" ")
            elif str(item.type) == 'BOOLEAN' :
                rowCSV.append('True' if getattr(record, str(item.name)) else 'False')
            elif str(item.type) == 'DATETIME' :
                rowCSV.append(getattr(record, str(item.name)).strftime("%m/%d/%Y %H:%M:%S"))
            else :
                rowCSV.append(getattr(record, str(item.name)))
    return rowCSV
  
def getFullPath(filename, folder = 'static/model-upload'):
    root_path = os.path.dirname(os.path.dirname(__file__))
    full_path = os.path.join(root_path, folder, filename)
    return full_path
