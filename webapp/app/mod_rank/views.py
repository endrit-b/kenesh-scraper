from flask import Blueprint, render_template

mod_rank = Blueprint('mod_rank', __name__)

@mod_rank.route('/', methods=['GET'])
def rank():
    '''
    Show rank page.
    '''
    return render_template('mod_rank/ranking.html')

