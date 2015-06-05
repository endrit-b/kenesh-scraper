from flask import Blueprint, Response
from app import mongo_utils
from bson import json_util

mod_api = Blueprint('mod_api', __name__, url_prefix='/api')

@mod_api.route('/absences', methods=['GET'])
def absentees():

    docs = mongo_utils.get_absences()

    resp = Response(
            response=json_util.dumps(docs),
            mimetype='application/json')

    return resp

@mod_api.route('/members/<string:party_type>', methods=['GET'])
def members(party_type):

    docs = mongo_utils.get_parliament_members(party_type)

    resp = Response(
            response=json_util.dumps(docs),
            mimetype='application/json')

    return resp

    