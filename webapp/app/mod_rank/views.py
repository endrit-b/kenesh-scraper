from flask import Blueprint, render_template
from app import mongo_utils

mod_rank = Blueprint('rank', __name__)

@mod_rank.route('/', methods=['GET'])
def rank():
    '''
    Show rank page.
    '''
    docs = mongo_utils.get_parliament_members()

    return render_template('mod_rank/ranking.html', members=docs)


@mod_rank.route('/<string:party_type>', methods=['GET'])
def rank_party_type(party_type):
    '''
    Show rank page.
    '''
    docs = mongo_utils.get_parliament_members(party_type)

    return render_template('mod_rank/ranking.html', members=docs, party_type=party_type)

