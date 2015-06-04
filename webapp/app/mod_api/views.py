from flask import Blueprint, Response
from app import mongo_utils
from bson import json_util

mod_api = Blueprint('mod_api', __name__, url_prefix='/api')

@mod_api.route('/absentees', methods=['GET'])
def absentees():

    docs = mongo_utils.get_absentees()

    resp = Response(
            response=json_util.dumps(docs),
            mimetype='application/json')

    return resp