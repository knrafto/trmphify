import re
import sys
import webbrowser
import urllib.request

import bs4
import flask

app = flask.Flask(__name__)

@app.route('/')
def hello_world():
    return flask.current_app.send_static_file('index.html')

MOVE_LIST_RE = re.compile(r'Move List')
SIZE_RE = re.compile(r'Size (\d+)')

def download_soup(url):
    r = urllib.request.urlopen(url).read()
    return bs4.BeautifulSoup(r, 'html.parser')

def scrape_moves(soup):
    for tag in soup.find(text=MOVE_LIST_RE).find_parent(class_='portlet').find_all('b'):
        yield str(tag.string).split('.')[-1]

def scrape_size(soup):
    text = str(soup.find(text=SIZE_RE))
    return int(SIZE_RE.search(text).group(1))

def swap_move(move):
    a, b = ord(move[0]) - ord('a'), int(move[1:]) - 1
    return chr(b + ord('a')) + str(a + 1)

# if __name__ == '__main__':
#     if len(sys.argv) != 2:
#         print('usage: {} [Little Golem Game ID]'.format(sys.argv[0]), file=sys.stderr)
#         sys.exit(1)
#     url = 'https://www.littlegolem.net/jsp/game/game.jsp?gid=' + sys.argv[1]
#     soup = download_soup(url)
#     moves = []
#     for move in scrape_moves(soup):
#         if move == 'resign':
#             pass
#         elif move == 'swap':
#             move = swap_move(moves[-1])
#             moves = [move, move]
#         else:
#             moves.append(move)
#     size = scrape_size(soup)
#     webbrowser.open('http://trmph.com/hex/board#{},{}'.format(size, ''.join(moves)))