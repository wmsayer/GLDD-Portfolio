from urllib import parse
import json


# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Utility API routes
@app.route('/api/<query_uri>', methods=['GET'])
def api_sql(query_uri):
    """
    This API will execute any query passed in the route
    :param query_uri: URI encoded SQL query
    :return: JSON of query results
    """
    conn = eng.connect()
    if request.method == 'GET':
        query = parse.unquote(query_uri)
        return query_data(query, conn, 'json')


@app.route('/MTNN/<json_uri>', methods=['GET'])
def movie_trait_network(json_uri):
    """
    if 'tConst' empty, returns compatibilities for top 5 most compatible genres
    if 'tConst' non-empty, calculates personalized ratings for movies in 'tConst'
    :param json_uri: {'userId':[int, ...], 'tConst': [int, int, ...]}
    :return:
    """
    if request.method == 'GET':
        with eng.connect() as conn:
            json_dict = json.loads(parse.unquote(json_uri))
            result_df = handle_mtnn_api(json_dict, mt_model, conn)
        return Response(result_df.to_json(orient="records"), mimetype='application/json')

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# WebApp API routes (CRUD)
@app.route('/read/<table>/<json_uri>', methods=['GET'])
def read(table, json_uri):
    conn = eng.connect()
    if request.method == 'GET':
        json_dict = json.loads(parse.unquote(json_uri))
        result = jsonify({'status': "Table not recognized"})

        if table == "Movies":
            q_table = table[:-1] + "Summary"
            if "userId" in json_dict.keys():
                result = personalized_movie_search(q_table, json_dict, mt_model, conn)
            else:
                query = build_general_read_query(q_table, json_dict, "AND")
                result = query_data(query, conn, 'json')

        if table == "Cocktails":
            q_table = table[:-1] + "Summary"
            if "userId" in json_dict.keys():
                json_dict.pop("userId")
            query = build_general_read_query(q_table, json_dict, "AND")
            result = query_data(query, conn, 'json')

        if table == "User":
            query = build_user_query(json_dict)
            result = query_data(query, conn, 'json')

        if table == "UserAuto":
            query = build_user_autocomplete(json_dict)
            result = query_data(query, conn, 'json')

        return result


@app.route('/delete/<table>/<item_id>', methods=['GET'])
def delete(table, item_id):
    if request.method == 'GET':
        conn = eng.connect()

        if table == 'Movie':
            sel_query = 'SELECT * FROM Movie WHERE tConst = %s' % item_id
            result = query_data(sel_query, conn, 'json')
            del_query = 'DELETE FROM Movie WHERE tConst = %s' % item_id
        else:
            sel_query = 'SELECT * FROM CocktailRecipe WHERE recipeId = %s' % item_id
            result = query_data(sel_query, conn, 'json')
            del_query = 'DELETE FROM CocktailRecipe WHERE recipeId = %s' % item_id

        conn.execute(del_query)
        return result


@app.route('/add/<table>/<new_input>', methods=['GET'])
def insert(table, new_input):
    conn = eng.connect()
    json_dict = json.loads(parse.unquote(new_input))

    if table == "Cocktail":
        if "userId" in json_dict.keys():
            json_dict.pop("userId")
        if "recipeId" in json_dict.keys():
            json_dict.pop("recipeId")
        handle_recipe_action(json_dict, conn, "insert")

    if table == "Movie":
        handle_add_movie(json_dict, conn, "insert")

    else:
        query = build_insert_query(table, json_dict)
        conn.execute(query)

    response = {'status': 'success', 'message': 'Record added successfully'}
    return jsonify(response)


@app.route('/edit/<table>/<item_id>/<title>', methods=['GET'])
def edit_user(table, item_id, title):
    conn = eng.connect()

    if table == "User":
        trs = title.split(':')
        query = "UPDATE User SET trOpen = '%s',trCon = '%s',trex = '%s',trAg = '%s',trNe = '%s' WHERE (userId = %s)" % (trs[0],trs[1],trs[2],trs[3],trs[4], item_id)
        conn.execute(query)

    response = {'status': 'success', 'message': 'Product edit successfully'}
    return response


@app.route('/edit/<table>/<json_uri>', methods=['GET'])
def edit(table, json_uri):
    conn = eng.connect()
    json_dict = json.loads(parse.unquote(json_uri))

    if table == "Movie":
        update_dict = {"tConst": json_dict["tConst"],
                       "title": json_dict["title"],
                        "year": json_dict["year"]}
        query = build_update_query(table, update_dict, 'tConst')
        conn.execute(query)

    elif table == "Cocktail":
        if "userId" in json_dict.keys():
            json_dict.pop("userId")
        handle_recipe_action(json_dict, conn, "update")

    response = {'status': 'success', 'message': 'Product edit successfully'}
    return response


@app.route('/vote/<table>/<json_uri>', methods=['GET'])
def vote(table, json_uri):
    conn = eng.connect()
    json_dict = json.loads(parse.unquote(json_uri))

    if table == "Movie":
        vote_table = "FavoriteMovie"
        vote_col = "ratesMovie"
        handle_vote(vote_table, vote_col, json_dict, conn)

    response = {'status': 'success', 'message': 'Product edit successfully'}
    return response


if __name__ == "__main__":
    app.run()
