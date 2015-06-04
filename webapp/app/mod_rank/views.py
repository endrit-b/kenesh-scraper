from flask import Blueprint, render_template
from flask.views import View

mod_rank = Blueprint('rank', __name__)

@mod_rank.route('/', methods=['GET'])
def rank():
    '''
    Show rank page.
    '''
    return render_template('mod_rank/ranking.html')

