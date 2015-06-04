from flask import Blueprint, render_template
from app import mongo_utils

mod_rank = Blueprint('rank', __name__)

@mod_rank.route('/', methods=['GET'])
def rank():
    '''
    Show rank page.
    '''

    docs = mongo_utils.get_absentees()

    return render_template('mod_rank/ranking.html', absentees=docs)

