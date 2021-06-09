from application.server.MovieTraitNetwork import *
from application.server.SQLAdmin import *
# from MovieTraitNetwork import *
from flask import jsonify
import pandas as pd
import json
# import sql_api


def query_data(query, conn, return_type):
    q_data = conn.execute(query)
    # result = (1, 2, 3,) or result = ((1, 3), (4, 5),)
    try:
        result_data = [dict(zip(tuple(q_data.keys()), i)) for i in q_data.cursor]
    except TypeError:
        result_data = []

    if query:
        message = "No results found"
    else:
        message = "Query empty"

    if result_data:
        message = "Results found"

    if return_type == 'json':
        return jsonify({'data': result_data, 'status': message})

    if return_type == 'df':
        return pd.DataFrame(result_data), message


def personalized_movie_search(table, json_dict, model, conn):
    """ Returns JSON of movie query results for a specified user with added columns for "personalRating" and "ratesMovie"

    :param table: "MovieSummary"
    :param json_dict: { userId: (int), filterX: { value: "filterX_value", operator: "filterX_operator" }, ...}
    :param model: Neural Network Model connecting personality traits to genres
    :param conn:
    :return: JSON of movie query results with added columns for "personalRating" and "ratesMovie"
    """
    user_id = json_dict.pop("userId")

    # SELECT FROM MovieSummary WHERE filters...  to grab top 100 Movies within filter conditions
    query = build_general_read_query(table, json_dict, "AND")
    result_df, message = query_data(query, conn, 'df')

    # SELECT FROM FavoriteMovie WHERE filters...   to grab user's votes on all movies
    vote_filt_dict = {"userId": {'value': user_id, 'operator': '='}}
    votes_query = build_general_read_query("FavoriteMovie", vote_filt_dict, "AND", columns=['tConst', 'ratesMovie'])
    votes_df, message = query_data(votes_query, conn, 'df')

    if not result_df.empty:
        if not votes_df.empty:
            # join user's votes to the result dataframe; if user has not voted on a movie, value set to np.nan
            votes_df.set_index('tConst', inplace=True)
            result_df = result_df.join(votes_df, on='tConst', lsuffix='', rsuffix='_copy')
        else:
            # if user has not voted on any movie, set all vote values to np.nan
            result_df['ratesMovie'] = np.nan

        # read from neural network to get the user's personalRating (recommendation)
        feat_dict = {"userId": user_id, "tConst": list(result_df["tConst"].values)}
        compat_df = handle_mtnn_api(feat_dict, model, conn)
        result_df["personalRating"] = compat_df["personalRating"]

        # remove NaN values
        idx = pd.IndexSlice
        mask = pd.isnull(result_df['ratesMovie'])
        result_df.loc[idx[mask], 'ratesMovie'] = 0
        mask = pd.isnull(result_df['personalRating'])
        result_df.loc[idx[mask], 'personalRating'] = 0

    json_rec = result_df.to_dict(orient="records")
    return jsonify({'data': json_rec, 'status': message})


def handle_mtnn_api(json_dict, model, conn):
    """
    if 'tConst' empty, returns compatibilities for top 5 most compatible genres
    if 'tConst' non-empty, calculates personalized ratings for movies in 'tConst'

    :param json_dict: {'userId':[int, ...], 'tConst': [int, int, ...]}
    :param model: neural network model
    :param conn:
    :return:
    """
    tconst_list = json_dict.pop('tConst')

    # SELECT user's information (i.e. personality trait values)
    user_info_df, message = query_data(build_user_query(json_dict), conn, 'df')

    # SELECT tConst, rating, and genreNames for movies in tConst_list
    genre_query = build_genres_query(tconst_list)
    genre_df, message = query_data(genre_query, conn, 'df')

    # calculate the user's compatability with each movie; ultimately joins 'user_info_df' and 'genre_df'
    # and adds new column for 'personalRating'
    result = calc_genre_compat(user_info_df, tconst_list, genre_df, model)

    return result


def handle_vote(vote_table, vote_col, json_dict, conn):
    """ First SELECTs to check to see if the user has already voted on this item
            - if so then it updates the vote
            - if not then it inserts a new vote

    :param vote_table: (str) (i.e. FavoriteMovie, FavoriteCocktail, FavoritePair)
    :param vote_col: (str) (i.e. ratesMovie, ...)
    :param json_dict: {col_name1: value1, ...}
    """
    # used in SELECT query
    match_filters = preformat_filter_dict(json_dict, "=")

    # stores value of the new vote to be placed
    new_val_filter = {vote_col: match_filters.pop(vote_col)}

    # SELECT...WHERE userId = ..., tConst/cocktailId = ...
    read_query = build_general_read_query(vote_table, match_filters, "AND")
    check_df, message = query_data(read_query, conn, 'df')

    if check_df.empty:
        # if user has not already placed a vote on this movie INSERT a new vote
        query = build_insert_query(vote_table, json_dict)
    else:
        # if user has already placed a vote on this movie UPDATE the value of the vote to the new vote
        filter_str = build_filters(match_filters)
        where_clause_str = build_where(filter_str, relationship="AND")
        query = "UPDATE %s SET %s \n" % (vote_table, build_filters(new_val_filter)[0])
        query += where_clause_str

    conn.execute(query)


def check_then_insert(table, check_dict, id_col, conn):
    """ This function checks to see if the new values exist already:
            - if the value exists SELECTs the value's corresponding id
            - if the value does not exist it INSERTs the new value and then SELECTs the new id
    :return: (int) id value, (boolean) if value was preexisting

    :param table: (str) name of table to check (i.e. CocktailName)
    :param check_dict: {check_col: new_value}, check_col - name of column to check in table to check (i.e. "cocktailName")
    :param id_col: (str) name of id column in table to check (i.e. "cocktailId")
    :param conn: database connection
    :param action: "insert" or "update"
    """
    # format filters for use in build_general_read_query
    filter_dict = preformat_filter_dict(check_dict, "=")

    # build the SELECT query that will check to see if cocktailName/glasswareName exist
    check_query = build_general_read_query(table, filter_dict, "AND")

    # execute check_query and return results as a pandas dataframe
    check_df, message = query_data(check_query, conn, 'df')

    if check_df.empty:
        print("Value not found, inserting new tuple into %s." % table)
        # builds INSERT query to insert new cocktailName/glasswareName
        insert_query = build_insert_query(table, check_dict)
        conn.execute(insert_query)

        # execute check_query and return results as a pandas dataframe
        check_df, message = query_data(check_query, conn, 'df')
    else:
        print("Value exists, not inserting new tuple into %s." % table)

    # grabs and returns id value (integer) from results, as well as if the return id is result of preexisting tuple
    return check_df[id_col][0]


def handle_recipe_action(json_dict, conn, action):
    """This function uses Python logic to perform a Compound Statement:
            - loops through the SQL tables in the "checks" dictionary to check if the new values exist already
                - if the value exists in "checkCol" it SELECTs the value's corresponding id
                - if the value does not exist in "checkCol" it INSERTs the new value and then SELECTs the new id
            - those id values are used in the final_query to "CocktailRecipe" whether it is INSERT or UPDATE

    :param json_dict: {column_name1: new_val1, ....}
    :param conn: database connection
    :param action: (str) either "insert" or "update" to determine final_query at the end
    """

    checks = {"CocktailName": {"checkCol": "cocktailName", "idCol":  "cocktailId"},
              "Glassware": {"checkCol": "glasswareName", "idCol":  "glasswareId"}}

    # loop through all tables where we need to ensure values already exist due to foreign key constraints
    for table_name, check_info in checks.items():
        check_col = check_info["checkCol"]
        id_col = check_info["idCol"]

        if check_col in json_dict.keys():
            # grabs cocktailName/glasswareName (for use in check_then_insert())
            # pops from json_dict as cocktailName/glasswareName do not exist in CocktailRecipe table attributes
            check_val = "'" + json_dict.pop(check_col) + "'"

            # checks if value exists; if so -> returns id, if not -> inserts the new value then returns id
            check_id = check_then_insert(table_name, {check_col: check_val}, id_col, conn)

            # inserts id value into json_dict as cocktailId/glasswareId do exist in CocktailRecipe table attributes
            json_dict[id_col] = check_id

    final_query = ""
    if action == "insert":
        # builds INSERT query to insert new CocktailRecipe
        final_query = build_insert_query("CocktailRecipe", json_dict)

    if action == "update":
        if "ingredients" in json_dict.keys():
            json_dict.pop("ingredients")
        if "rating" in json_dict.keys():
            json_dict.pop("rating")
        # builds UPDATE query to update CocktailRecipe
        final_query = build_update_query("CocktailRecipe", json_dict, "recipeId")

    conn.execute(final_query)


def handle_add_movie(json_dict, conn, action):
    """ This function expects the following input to perform two INSERT actions
    json_dict = {
                  title: (str),
                  year: (int),
                  genre: (int)
                }
    """
    checks = {"Movie": {"checkCol": ["title", "year"], "idCol":  "tConst"}}
    final_dict = {"genreId": json_dict.pop("genre")}
    check_dict = {}

    # loop through all tables/columns where we need to ensure values already exist due to foreign key constraints
    for table_name, check_info in checks.items():
        check_cols = check_info["checkCol"]
        id_col = check_info["idCol"]

        for col in check_cols:
            if col in json_dict.keys():
                check_dict[col] = json_dict.pop(col)

        # checks if values exists; if so -> returns id, if not -> inserts the new value then returns id
        new_id = check_then_insert(table_name, check_dict, id_col, conn)

        # inserts id value into json_dict
        final_dict[id_col] = new_id

    if action == "insert":
        genre_query = build_insert_query("MovieCategory", final_dict)
        print(genre_query)
        conn.execute(genre_query)


if __name__ == '__main__':
    print("Test with sql_api.py or tests.py")



