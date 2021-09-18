from . import or_
from . import request
from . import desc, asc
# Utility function controller

def GetTableColumn(Table, col_exclude):
    colObj = {}
    columns = []
    for col_name in Table.__table__.columns.keys() :
        if col_name not in col_exclude :
            colObj[ col_name ] = col_name.replace("_", " ").title()
    return colObj


def GetTableHeader(Table, col_exclude, sort_exclude, overide_label):
    tableHeader = GetTableColumn(Table, col_exclude)
    for label in overide_label:
        tableHeader[label] = overide_label[label]

    for column in tableHeader:
        tableHeader[column] = [tableHeader[column], column not in sort_exclude]

    return tableHeader

def getTableRecords(Table, search_key, filters, sort_type, _col, page, per_page):
    filtersObj = [
        getattr(Table, filter).like(search_key) for filter in filters
    ]

    baseQuery = Table().query.filter(
                                or_(*filtersObj)
                            ).order_by(
                                sort_type(getattr(Table, _col))
                            )
    tableRecords = baseQuery.paginate(page, per_page, error_out=False)
    min_page = tableRecords.page - 2 if tableRecords.page - 2 > 0 else 1
    max_page = min_page + 5 if min_page + 5 <= tableRecords.pages + 1 else tableRecords.pages + 1
    count = baseQuery.count()

    return tableRecords, min_page, max_page, count

def initTableRecords(per_page=10):
    page = request.args.get('page')
    page = int(1 if page == None else page)

    table_search = ""
    search_key = "%%"

    _col = 'id'
    _type = 'desc'
    sort_type = desc

    if request.method == "POST" :
        if 'table_search' in request.form : 
            table_search = request.form["table_search"]
            search_key = "%{}%".format(table_search)
        if 'sort' in request.form :
            _type = request.form["sort"]
            _col = request.form["column"]
            sort_type = desc if _type == 'desc' else asc

    return page, per_page, table_search, search_key, _col, _type, sort_type