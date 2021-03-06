import logging
import re
import os

import bs4
import flask
import requests

app = flask.Flask(__name__, static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

@app.before_first_request
def set_up_logging():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_and_redirect():
    game = flask.request.form.get('game', '')
    try:
        url = convert(game)
        app.logger.info('Game "{}" converted to {}'.format(game, url))
    except ConversionException as e:
        flask.flash(str(e))
        app.logger.warning('Game "{}" conversion failed ({})'.format(game, str(e)))
        url = flask.url_for('index')
    return flask.redirect(url)

SIZE_REGEX = re.compile(r'^\s*Hex( [^-]+)?-Size (\d+)')
MOVE_LIST_REGEX = re.compile(r'Move List')
MOVE_REGEX = re.compile(r'[a-z]\d{1,2}')

class ConversionException(Exception):
    pass

def maybe(x):
    if not x:
        raise ConversionException('Could not determine game moves')
    return x

def convert(game):
    game = game.strip()
    if not game:
        raise ConversionException('Enter a Little Golem URL or game ID')
    if game.startswith('#'):
        game = game[1:]
    if 'littlegolem.net' in game:
        url = game
    else:
        url = 'https://littlegolem.net/jsp/game/game.jsp?gid=' + game
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        html = response.text
    except requests.exceptions.RequestException:
        raise ConversionException('Could not download game')
    soup = bs4.BeautifulSoup(html, 'html.parser')
    title = maybe(soup.find(class_='page-title')).text
    size = int(maybe(re.search(SIZE_REGEX, title)).group(2))
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
