# from application.server.MovieTraitNetwork import *
# from MovieTraitNetwork import *
# from flask import jsonify
import pandas as pd
# import sql_api


def build_filters(filter_dict):
    """
    This function takes a dictionary of filters where each filter stores a dictionary containing the filter value and
    SQL operator to be used on the filter.
    :param filter_dict: dictionary of filters { filterX: { value: "filterX_value", operator: "filterX_operator" }, ...}
    :return: list of filters formatted for SQL WHERE clause
    """
    filter_strs = []
    for (filterX, options) in filter_dict.items():
        filter_val = options['value']
        operator = options['operator']

        if isinstance(filter_val, str) and filter_val:
            if operator == 'LIKE':
                # filter_val = "'%%" + filter_val + "%%'"
                filter_val = "%%" + filter_val + "%%"

            if not ((filter_val[0] == "'" or filter_val[0] == '"') and (filter_val[-1] == "'" or filter_val[-1] == '"')):
                filter_val = repr(filter_val)

            filter_strs.append(filterX + " " + operator + " " + filter_val)

        if not isinstance(filter_val, str):
            filter_strs.append(filterX + " " + operator + " " + repr(filter_val))

    return filter_strs


def build_where(filter_strs, relationship="AND"):
    """
    This function builds the WHERE clause string from a list of filters' strings which have been preformmated for the
    SQL WHERE clause.
    :param filter_strs: list of preformatted filter strings ["location LIKE %%Los Angeles%%", "rating >= 5"]
    :param relationship: str "AND", "OR"
    :return: complete, formatted WHERE clause string to be concatenated into SQL query
    """
    where_str = ""
    if filter_strs:
        where_str += "WHERE " + filter_strs[0] + "\n"

        if len(filter_strs) > 1:
            for f in filter_strs[1:]:
                where_str += " " + relationship + " " + f + "\n"
    return where_str


def build_col_str(columns):
    count = 0
    col_str = ""

    for col in columns:
        if count > 0:
            col_str += ", "
        col_str += col
        count += 1

    return col_str


def build_general_read_query(table, json_dict, filter_rel, columns=None):
    if columns is None:
        columns = []
    if columns:
        col_str = build_col_str(columns)
        query = "SELECT %s FROM %s\n" % (col_str, table)
    else:
        query = "SELECT * FROM %s\n" % table

    filter_str = build_filters(json_dict)
    where_clause_str = build_where(filter_str, relationship=filter_rel)
    query += where_clause_str
    query += "LIMIT 100"
    return query


def build_user_query(json_dict):
    query = "SELECT userId, firstName, lastName, emailId, trOpen, trCon, trEx, trAg, trNe\n" \
            "FROM User\n"

    if 'userId' in json_dict.keys():
        user_ids = json_dict['userId']

        # if searching for multiple users, 'user_ids' should be a list of the userId's
        # if searching for a single user, 'user_ids' can be int or int nested in a list
        # this code will convert user_ids to list if it is not
        if not isinstance(user_ids, list):
            user_ids = [user_ids]

        user_filters = []
        for uid in user_ids:
            user_filters += build_filters({'userId': {'value': uid, 'operator': "="}})

        where_str = build_where(user_filters, relationship="OR")
    else:
        filter_dict = {}

        user_email = "'" + json_dict['emailId'] + "'"
        filter_dict['emailId'] = {'value': user_email, 'operator': "="}

        user_password = "'" + json_dict['password'] + "'"
        filter_dict['password'] = {'value': user_password, 'operator': "="}

        user_filters = build_filters(filter_dict)
        where_str = build_where(user_filters, relationship="AND")

    query += where_str
    return query


def build_genres_query(tconst_list):
    if tconst_list:
        query = "SELECT MovieCategory.tConst, Movie.rating, Genre.genreName\n" \
                "FROM Genre\n" \
                " LEFT JOIN MovieCategory ON Genre.genreId = MovieCategory.genreId\n" \
                " LEFT JOIN Movie ON MovieCategory.tConst = Movie.tConst\n"

        filter_str = []
        for tconst in tconst_list:
            filter_str.append("MovieCategory.tConst = %d" % tconst)

        where_str = build_where(filter_str, relationship="OR")
        query += where_str
    else:
        query = "SELECT Genre.genreName\n" \
                "FROM Genre"

    return query


def build_insert_query(query_dict, type="records"):

    if type == "records":
        # key_str = repr(query_dict["columns"])[1:-1]
        val_str = ""
        key_str = ""

        for rec in query_dict["records"]:
            temp_key_str, temp_val_str = json_to_cs_str(rec)

            if val_str:
                val_str += ",\n"

            val_str += "(" + temp_val_str + ")"
            key_str = temp_key_str

    else:
        key_str, val_str = json_to_cs_str(query_dict)
        val_str = "(" + val_str + ")"

    query = "INSERT INTO %s (%s)" \
            "\n VALUES \n%s\n" % (query_dict["table"], key_str, val_str)

    return query


def build_update_query(table, json_dict, match_col):
    formatted_dict = preformat_filter_dict(json_dict, "=")
    print(formatted_dict)
    match_val = {match_col: formatted_dict.pop(match_col)}
    print(formatted_dict)
    new_val_list = build_filters(formatted_dict)
    print(new_val_list)
    match_val_list = build_filters(match_val)

    new_val_str = ""
    count = 0
    for val in new_val_list:
        if count > 0:
            new_val_str += ", "
        new_val_str += val
        count += 1

    print(new_val_str)
    query = "UPDATE %s SET %s" \
            " WHERE (%s)" % (table, new_val_str, match_val_list[0])

    return query


def build_user_autocomplete(json_dict):
    """
    Expects JSON: {userId: int, firstName: str_val, lastName: str_val, emailId: str_val}
    """
    # userId filter gets "!=" operator
    user_id = {'userId': json_dict.pop('userId')}
    user_filter_dict = preformat_filter_dict(user_id, "!=")
    user_filter = build_filters(user_filter_dict)

    # firstName, lastName, emailId filters get LIKE operator
    filter_dict = preformat_filter_dict(json_dict, "LIKE")
    filter_list = build_filters(filter_dict)

    # concatenate filters with AND relationship
    filter_list += user_filter
    where_str = build_where(filter_list, relationship="AND")

    query = "SELECT * FROM User " + where_str
    return query


def json_to_cs_str(json_dict):
    key_str = ""
    val_str = ""
    count = 0

    for k, v in json_dict.items():
        if count > 0:
            key_str += ", "
            val_str += ", "

        if isinstance(v, str):
            if not (v[0] == '@' or ((v[0] == "'" or v[0] == '"') and (v[-1] == "'" or v[-1] == '"'))):
                # v = "'" + v + "'"
                v = repr(v)
        else:
            v = repr(v)

        key_str += k
        val_str += v
        count += 1

    return key_str, val_str


def preformat_filter_dict(json_dict, operator):
    filter_dict = {}

    for key, val in json_dict.items():
        filter_dict[key] = {'value': val, 'operator': operator}

    return filter_dict

