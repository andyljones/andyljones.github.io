import re
import yaml
import mistune
import jinja2
from pathlib import Path
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from feedgen.feed import FeedGenerator
from datetime import datetime
from email.utils import format_datetime

formatter = html.HtmlFormatter()

class HighlightRenderer(mistune.Renderer):

    def __init__(self, filename, **kwargs):
        self.filename = filename
        super().__init__(**kwargs)

    def block_code(self, code, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)
        lexer = get_lexer_by_name(lang, stripall=True)
        hl = highlight(code, lexer, formatter)
        return hl

    def image(self, src, title, text):
        return super().image(f'/source/{self.filename}/{src}', title, text)

def template():
    return jinja2.Template(Path('template.j2').read_text())

def markdown(filename=''):
    return mistune.Markdown(renderer=HighlightRenderer(filename))

def load(path):
    text = (Path(path) / 'index.md').read_text()
    meta, body = re.split('^---$', text, flags=re.MULTILINE)[1:]
    tags = yaml.safe_load(meta)
    if 'image' in tags:
        tags['image'] = 'https://andyljones.com/' + str(Path(path) / tags['image'])
    return tags, body

def sources():
    loaded = {}
    for post in Path('source').iterdir():
        if post.name == 'index':
            continue
        name, tags, body = (post.name, *load(post))
        loaded[tags['date'], name] = (tags, body)
    
    # Iterate in date order
    for (date, name) in sorted(loaded):
        yield (name, *loaded[date, name])

def posts():
    for name, tags, body in sources():
        content = markdown(name)(body)
        style = formatter.get_style_defs()
        html = template().render(content=content, style=style, **tags)
        
        (Path('posts') / (name + '.html')).write_text(html)

def post_links():
    lines = []
    for name, tags, _ in sources():
        if 'publish' in tags and not tags['publish']:
            print(f'Leaving {name} out of index')
            continue 
        lines.append(f'* [{tags["title"]}](posts/{name}.html): {tags["description"]}')
    return '\n'.join(lines[::-1])

def rss():
    gen = FeedGenerator()
    gen.id('andyljones.com')
    gen.title('andy l jones')
    gen.author({'name': 'Andy L Jones', 'email': 'me@andyljones.com'})
    gen.link(href='https://andyljones.com', rel='self')
    gen.logo('https://andyljones.com/icons/robot-solid.png')
    gen.description('Andy L Jones\' blog')
    gen.language('en')

    for name, tags, body in sources():
        if 'publish' in tags and not tags['publish']:
            print(f'Leaving {name} out of RSS feed')
            continue 
        url = 'https://andyljones.com/' + str(Path('posts') / (name + '.html'))
        entry = gen.add_entry()
        entry.id(url)
        entry.title(tags['title'])
        entry.description(tags['description'])
        entry.link(href=url)

        date = datetime.strptime(tags['date'], '%Y/%m/%d')
        entry.pubDate(format_datetime(date))
    gen.rss_str(pretty=True)
    gen.rss_file('rss.xml')

def index():
    tags, body = load('source/index')
    body = re.sub('{{posts}}', post_links(), body)
    content = markdown()(body)
    html = template().render(content=content, **tags)
    Path('index.html').write_text(html)
    
if __name__ == '__main__':
    print('Generating...')
    posts()
    rss()
    index()
    print('Generated')
