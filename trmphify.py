import re

import bs4
import flask
import requests

app = flask.Flask(__name__)
app.secret_key = 'bZEWlYuyqWZHPBPYgrwiBSlD'

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_and_redirect():
    game = flask.request.form.get('game', '')
    try:
        url = convert(game)
    except ConversionException as e:
        flask.flash(str(e))
        url = flask.url_for('index')
    return flask.redirect(url)

SIZE_REGEX = re.compile(r'Size (\d+)')
MOVE_LIST_REGEX = re.compile(r'Move List')
MOVE_REGEX = re.compile(r'[a-z]\d{1,2}')

class ConversionException(Exception):
    pass

def maybe(x):
    if not x:
        raise ConversionException('Could not determine game moves')
    return x

def convert(game):
    if not game:
        raise ConversionException('Enter a Little Golem URL or game ID')
    if game.startswith('http'):
        url = game
    else:
        url = 'https://littlegolem.net/jsp/game/game.jsp?gid=' + game
    try:
        response = requests.get(url, )
        response.raise_for_status()
        html = response.text
    except requests.exceptions.RequestException:
        raise ConversionException('Could not download game')
    soup = bs4.BeautifulSoup(html, 'html.parser')
    title = maybe(soup.find(class_='page-title')).text
    size = int(maybe(re.search(SIZE_REGEX, title)).group(1))
    move_list_tag = maybe(soup.find(text=MOVE_LIST_REGEX))
    move_list_box = maybe(move_list_tag.find_parent(class_='portlet'))
    moves = [tag.text.split('.', 1)[-1] for tag in move_list_box.find_all('b')]
    for i, move in enumerate(moves):
        if not any([
            move == 'resign' and i == len(moves) - 1,
            move == 'swap' and i == 1,
            re.match(MOVE_REGEX, move),
        ]):
            raise ConversionException('Could not determine game moves')
    return trmph_url(size, moves)

def swap_move(move):
    a, b = ord(move[0]) - ord('a'), int(move[1:]) - 1
    return chr(b + ord('a')) + str(a + 1)

def trmph_url(size, little_golem_moves):
    trmph_moves = []
    for move in little_golem_moves:
        if move == 'resign':
            pass
        elif move == 'swap':
            move = swap_move(little_golem_moves[0])
            trmph_moves = [move, move]
        else:
            trmph_moves.append(move)
    return 'http://trmph.com/hex/board#{},{}'.format(size, ''.join(trmph_moves))
