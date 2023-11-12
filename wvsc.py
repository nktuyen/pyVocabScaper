import os
from optparse import OptionParser
import bs4
import sqlite3
import json
import enchant
from multiprocessing import Lock
import concurrent.futures
#import gevent.monkey
#gevent.monkey.patch_all()
import requests

class ScapingInfo:
    def __init__(self, url: str, session: requests.Session, handle, locker: Lock = None, verbose: bool = False) -> None:
        self._url = url
        self._session = session
        self._handle = handle
        self._locker = locker
        self._verbose = verbose

    @property
    def url(self) -> str:
        return self._url
    
    @property
    def session(self) -> requests.Session:
        return self._session
    
    @property
    def locker(self) -> Lock:
        return self._locker
    
    @property
    def handle(self):
        return self._handle
    
    @property
    def verbose(self) -> bool:
        return self._verbose

sess: requests.Session = requests.Session()
locker: Lock = Lock()
words: dict = {}
output: str = ''
handle = None

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, bs4.element.Comment):
        return False
    return True

def split_text(texts: list, sep: str = ' ') -> list:
    l = []
    for t in texts:
        tmp = t.split(sep)
        for e in tmp:
            if len(e.strip()) > 0:
                l.append(e.strip().lower())
    return l

def scrap(url: str) -> dict:
    print(f'Scraping {url}')
    user_agent: dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'}
    response: requests.Response = None
    try:
        response = sess.get(url, headers=user_agent, timeout=10, allow_redirects=False)
    except Exception as ex:
        print(f'[Exception]:{ex}')
        return {}
    
    if response is None:
        return {}
    if response.status_code != 200:
        print(f'Status code:{response.reason}')
        return {}
    
    content_type: str = response.headers.get('content-type')
    print(f'Content-Type:{content_type}')
    if 'text/html' not in content_type.lower():
        return {}
    if not isinstance(response.text, str):
        return {}
    
    soup:bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, 'html.parser')
    response.close()
    dic: enchant.Dict = enchant.Dict('en_US')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    for text in visible_texts:
        vocabs = text.split(' ')
        for sep in "`~!@#$%^&*()_+`1234567890-=[]{{}}\\|;:'"",<.>/?":
            vocabs = split_text(vocabs, sep)
        for voc in vocabs:
            if dic.check(voc):
                if voc in words:
                    words[voc] = words[voc] + 1
                else:
                    words[voc] = 1
                print(f'{voc}:{words[voc]}')
    return words

if __name__=="__main__":
    parser: OptionParser = OptionParser('%prog [OPTIONS] URL(s)')
    parser.add_option('-v','--verbose', default=False, help='Verbose output')
    parser.add_option('-i','--input', default=None, help='Input file which contains URL(s) to browse')
    parser.add_option('-o','--output', default='b.sqlite3', help='Output file to store vocabularies. Default is b.sqlite3')

    opts, args = parser.parse_args()
    urls: list = []
    for arg in args:
        if arg.lower().startswith('http://') or arg.lower().startswith('https://'):
            urls.append(arg.strip())
        else:
            print(f'Invalid url:{arg}')
            exit(1)
    verbose: bool = False
    if opts.verbose is not None:
        verbose = opts.verbose

    #Output file validation
    if opts.output is None:
        print("Output file is not specified!")
        exit(2)
    
    output = os.path.abspath(str(opts.output))
    if (not output.lower().endswith('.sqlite3'))and(not output.lower().endswith('.json')) and(not output.lower().endswith('.txt')):
        print(f'Output file extension is not supported:{output}!\nOnly .sqlite3/.json and .txt are supported!')
        exit(3)
    
    #Input file validation
    if opts.input is not None:
        inp: str = os.path.abspath(opts.input)
        if not os.path.isfile(inp):
            print(f'{inp} is not valid file!')
            exit(4)
        if inp.lower().endswith('.sqlite3'):
            conn: sqlite3.Connection = None
            try:
                conn = sqlite3.connect(inp)
                res = conn.cursor().execute("SELECT url FROM urls")
                rows = res.fetchall()
                for row in rows:
                    urls.append(row[0].strip())
                conn.close()
            except Exception as ex:
                print(f'[Exception]:{ex}')
                exit(5)
        else:
            try:
                with open(inp, 'r') as inp_file:
                    if inp.lower().endswith('.json'):
                        lines = json.load(inp_file)
                    else:
                        lines = inp_file.readlines()
                    for line in lines:
                        urls.append(line.strip())
            except Exception as ex:
                print(f'[Exception]:{ex}')
                exit(6)

    if len(urls) <= 0:
        print("No url specified!")
        exit(7)

    #Load current vocabularies in output file if exist
    if output.lower().endswith('.sqlite3'):
        try:
            handle = sqlite3.connect(output)
            cur = handle.cursor()
            table_exist: bool = False
            result = cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
            for row in result.fetchall():
                if 'vocabularies' in row:
                    table_exist = True
                    break
            if not table_exist:
                cur.execute('CREATE TABLE vocabularies(id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL UNIQUE, occurrences INTEGER)')
                for ch in ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','x','y','z','w']:
                    cur.execute('INSERT INTO vocabularies(name,occurrences) VALUES(?,?)', (ch, 1,))
                    words[ch] = 1
                handle.commit()
            else:
                result = handle.execute('SELECT name,occurrences FROM vocabularies')
                rows = result.fetchall()
                for row in rows:
                    words[row[0]] = row[1]
                if len(words) <= 0:
                    for ch in ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','x','y','z','w']:
                        cur.execute('INSERT INTO vocabularies(name,occurrences) VALUES(?,?)', (ch, 1,))
                        words[ch] = 1
                    handle.commit()
        except Exception as ex:
            print(f'[Exception]:{ex}')
            exit(8)
    else:
        if os.path.isfile(output):
            try:
                with open(output, 'r') as voc_file:
                    if output.lower().endswith('.json'):
                        words = json.load(voc_file)
                    else:
                        vocabulary: str = ''
                        occurences: int = 0
                        for line in voc_file.readlines():
                            word_occuren: list = line.strip().split(':')
                            vocabulary: str = ''
                            occurences: int = 0
                            if len(word_occuren) > 0:
                                vocabulary = word_occuren[0]
                            if len(word_occuren) > 1:
                                if str.isnumeric(word_occuren[1]):
                                    occurences = int(word_occuren[1])
                                else:
                                    print(f'Invalid vocabulary data:{word_occuren}')
                                    continue
                            words[vocabulary] = occurences
            except Exception as ex:
                print(f'[Exception]:{ex}')
                exit(9)
        handle = open(output, 'w')
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        future_to_url = (executor.submit(scrap, url) for url in urls)
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                vocabularies = future.result()
                words.update(vocabularies)
                locker.acquire()
                if isinstance(handle, sqlite3.Connection):
                    for w in words:
                        #print(w)
                        handle.cursor().execute('INSERT INTO vocabularies(name, occurrences) VALUES(?,?)', (w, words[w],))
                    handle.commit()
                else:
                    if output.lower().endswith('.json'):
                        json.dump(words, handle, indent=4)
                    else:
                        for w in words:
                            handle.write(f'{w}:{words[w]}\n')
                    handle.flush()
                locker.release()
            except Exception as ex:
                print(f'[Exception]:{ex}')
                continue