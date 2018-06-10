#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from common.utility import Stack
from ts_log import logger


class ArticleElem(object):
    # class variables
    depth = 0
    debug = False
    translator = None

    def __init__(self, article_type, article_text='', img_alt='', img_src=''):
        self.type = article_type
        self.text = article_text
        self.img_alt = img_alt
        self.img_src = img_src
        self.children = list()

    @staticmethod
    def set_translator(tr):
        ArticleElem.translator = tr

    def add(self, elem):
        self.children.append(elem)

    def to_str(self):
        ArticleElem.depth += 1
        blank = '{0:{1}}'.format('', 4*self.depth)
        if self.type == 'IMG':
            text = '%s%s(%d)\talt: %s\tsrc: %s' % (blank, self.type, ArticleElem.depth, self.img_alt, self.img_src)
        else:
            text = '%s%s(%d)\t%s\n' % (blank, self.type, ArticleElem.depth, self.text)
        for d in self.children:
            text += '\n' + blank + d.to_str()
            ArticleElem.depth -= 1
        return text

    def translate(self):
        if len(self.text) > 0:
            logger.debug("%s: %s\n" % (type, self.text))
            if self.type not in ['IMG', 'TABLE', 'BLOCKQUOTE'] and ArticleElem.translator:
                self.text = ArticleElem.translator.translate(self.text)
                logger.debug("%s: %s\n" % (type, self.text))

        for d in self.children:
            d.translate()

    def to_html(self, article_node, html_node=None, soup=None):
        ArticleElem.depth += 1

        # html root node
        html_tag = None
        if not html_node:
            html_str = '<html xmlns="http://www.w3.org/1999/xhtml" class="widthauto"></html>'
            soup = BeautifulSoup(html_str, 'lxml')
            html_tag = soup.html

            head_tag = soup.new_tag('head')
            html_tag.append(head_tag)

            meta_tag = soup.new_tag('meta')
            meta_tag['http-equiv'] = "Content-Type"
            meta_tag['content'] = "text/html; charset=gbk"
            head_tag.append(meta_tag)

            html_node = soup.html

        if ArticleElem.debug:
            embed_str = '{0:{1}}'.format('', 4 * ArticleElem.depth)
            logger.debug('\n%s%s(%d)\t%s\n' % (embed_str, article_node.type, ArticleElem.depth, article_node.text))

        if article_node.type == 'BODY':
            body_tag = soup.new_tag('body')
            html_tag.append(body_tag)
            html_node = body_tag
        elif article_node.type == 'DIV':
            div_tag = soup.new_tag('div')
            div_tag.string = article_node.text
            html_node.append(div_tag)
            html_node = div_tag
        elif article_node.type == 'PARA':
            p_tag = soup.new_tag('p')
            p_tag.string = article_node.text
            html_node.append(p_tag)
            html_node = p_tag
        elif article_node.type == 'HEAD':
            h2_tag = soup.new_tag('h2')
            h2_tag.string = article_node.text
            html_node.append(h2_tag)
            html_node = h2_tag
        elif article_node.type == 'IMG':
            img_tag = soup.new_tag('img')
            img_tag['class'] = "img-responsive"
            img_tag['alt'] = article_node.img_alt
            img_tag['src'] = article_node.img_src
            html_node.append(img_tag)
            html_node = img_tag
        elif article_node.type == 'TABLE':
            # enclosed the table in <p> tag
            html_node['class'] = "table-responsive"

            # convert table string to table tag tree
            table_soup = BeautifulSoup(article_node.text, 'html.parser')
            table_tag = table_soup.table
            table_tag['class'] = "table table-bordered table-striped"
            html_node.append(table_tag)
            html_node = table_tag
        else:
            pass

        # visit children
        for child in article_node.children:
            self.to_html(child, html_node, soup)

        ArticleElem.depth -= 1
        return soup


# non-recursive converting function
def to_html(root):
    html_str = '<html xmlns="http://www.w3.org/1999/xhtml" class="widthauto"></html>'
    soup = BeautifulSoup(html_str, 'lxml')

    head_tag = soup.new_tag('head')
    soup.html.append(head_tag)

    meta_tag = soup.new_tag('meta')
    meta_tag['http-equiv'] = "Content-Type"
    meta_tag['content'] = "text/html; charset=gbk"
    head_tag.append(meta_tag)

    # deep first walk-through tree
    stack = Stack()
    stack.push(root)
    stack_depth = 1
    visited = dict()
    visited[root] = True

    # visit root
    logger.debug('\n%s(%d)\t%s\n' % (root.type, stack_depth, root.text))
    while not stack.empty():
        # visit stack top element
        elem = stack.peek()

        # if the node has children nodes that is not visited
        if len(elem.children) > 0:
            visited_child_flag = False
            for child in elem.children:
                if child not in visited:
                    # push to stack
                    stack.push(child)
                    stack_depth += 1
                    visited_child_flag = True

                    # visit the un-visited child node
                    visited[child] = True
                    embed_str = '{0:{1}}'.format('', 4 * (stack_depth - 1))
                    logger.debug('\n%s%s(%d)\t%s\n' % (embed_str, child.type, stack_depth, child.text))

                    if child.type == 'DIV':
                        div_tag = soup.new_tag('div')
                        div_tag.string = child.text

                    elif child.type == 'PARA':
                        p_tag = soup.new_tag('p')
                        p_tag.string = child.text
                    break
            if visited_child_flag:
                # continue while loop
                continue
        stack.pop()
        stack_depth -= 1
    return soup


def test_gen_html():
    logger.debug('test')
    html_str = '<html xmlns="http://www.w3.org/1999/xhtml" class="widthauto"></html>'
    soup = BeautifulSoup(html_str, 'lxml')

    head_tag = soup.new_tag('head')
    soup.html.append(head_tag)

    meta_tag = soup.new_tag('meta')
    meta_tag['http-equiv'] = "Content-Type"
    meta_tag['content'] = "text/html; charset=gbk"
    head_tag.append(meta_tag)

    table_str = '''
<table><thead><tr><th>
<p><strong>Tax Break</strong></p>
</th>
<th>
<p><strong>Number of Taxpayers Claiming</strong></p>
</th>
<th>
<p><strong>Average Amount of Credit/Deduction</strong></p>
</th>
</tr></thead><tbody><tr><td width="175">
<p>Earned income tax credit</p>
</td>
<td width="138">
<p>28.1 million</p>
</td>
<td width="192">
<p>$2,440</p>
</td>
</tr><tr><td width="175">
<p>Child tax credit (includes additional child tax credit)</p>
</td>
<td width="138">
<p>22.4 million</p>
</td>
<td width="192">
<p>$2,399</p>
</td>
</tr><tr><td width="175">
<p>Deduction for state and local taxes paid</p>
</td>
<td width="138">
<p>44.2 million</p>
</td>
<td width="192">
<p>$12,514</p>
</td>
</tr></tbody></table>
'''
    # enclosed the table in <p> tag
    p_tag = soup.new_tag('p')
    p_tag['class'] = "table-responsive"
    soup.html.append(p_tag)

    # convert table string to table tag tree
    table_tag = BeautifulSoup(table_str, 'html.parser')
    p_tag.append(table_tag)

    #logger.debug(table_str)
    logger.debug('\n'+soup.prettify())


if __name__ == "__main__":
    test_gen_html()
