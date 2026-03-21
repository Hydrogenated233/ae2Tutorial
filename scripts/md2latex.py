#!/usr/bin/env python3
# encoding=utf-8

import sys
import re
import mistune
from mistune.renderers import BaseRenderer as Renderer

import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout.detach())
sys.stdin = codecs.getreader('utf8')(sys.stdin.detach())

class LaTeXRenderer(Renderer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.replace = True

    def finalize(self, data):
        return data

    def block_code(self, code, lang=None):
        code = code.rstrip('\n')
        if lang and code:
            code = self.escape(code)
            return '\\begin{lstlisting}[language=%s]\n%s\n\\end{lstlisting}\n\n' % (lang, code)
        if lang:
            lang, _, filename = lang[:-1].partition('[')
            return '\\lstinputlisting[language=%s, caption={%s}]{%s}\n\n' % (lang, self.escape(filename), filename)
        code = self.escape(code)
        return '\\begin{lstlisting}\n%s\n\\end{lstlisting}\n\n' % code

    def block_quote(self, text):
        return r'''\begin{tcolorbox}[
    colback=gray!5,
    colframe=gray!30,
    boxrule=0.5pt,
    left=12pt,
    right=12pt,
    top=6pt,
    bottom=6pt,
    arc=0pt,
    outer arc=0pt,
    boxsep=0pt,
    before skip=10pt,
    after skip=10pt,
    breakable
]
%s
\end{tcolorbox}

''' % text.rstrip('\n')

    def header(self, text, level, raw=None):
        levels = ['', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
        if level <= len(levels)-1:
            cmd = levels[level]
        else:
            cmd = 'subparagraph'
        return '\\%s{%s}\n\n' % (cmd, text)

    def hrule(self):
        return '\\hrule\n\n'

    def list(self, body, ordered=True):
        cmd = 'enumerate' if ordered else 'itemize'
        return '\\begin{%s}\n%s\\end{%s}\n\n' % (cmd, body, cmd)

    def list_item(self, text):
        return '\\item %s\n' % text

    def paragraph(self, text):
        return '%s\n\n' % text.strip(' ')

    def table(self, header, body):
        raise NotImplementedError

    def table_row(self, content):
        raise NotImplementedError

    def table_cell(self, content, **flags):
        raise NotImplementedError

    def double_emphasis(self, text):
        return '\\textbf{\\emph{%s}}' % text

    def emphasis(self, text):
        return '\\emph{%s}' % text

    def codespan(self, text):
        return '\\texttt{%s} ' % self.escape(text.rstrip())

    def linebreak(self):
        return '\\newline\n'

    def strikethrough(self, text):
        return '\\sout{%s}' % text

    def text(self, text):
        return self.escape(text)

    def escape(self, text):
        if not text:
            return ''
        newtext = ''
        in_math = False
        for c in text:
            if c == '$':
                in_math = not in_math
                newtext += c
                continue
            if not in_math:
                if c == '\\':
                    newtext += '\\textbackslash{}'
                elif c == '{':
                    newtext += '\\{'
                elif c == '}':
                    newtext += '\\}'
                elif c == '~':
                    newtext += '\\textasciitilde{}'
                elif c == '#':
                    newtext += '\\#'
                elif c == '%':
                    newtext += '\\%'
                elif c == '^':
                    newtext += '\\textasciicircum{}'
                elif c == '&':
                    newtext += '\\&'
                elif c == '_':
                    newtext += '\\_'
                else:
                    newtext += c
            else:
                newtext += c
        return newtext

    def autolink(self, link, is_email=False):
        return self.escape(link)

    def link(self, link, title, text):
        return '\\href{%s}{%s}' % (self.escape(link), self.escape(text))

    def image(self, src, title, text):
        if text:
            return '\\ref{%s}%%\n' \
                   '\\begin{figure}[htbp]\n' \
                   '    \\centering\n' \
                   '    \\includegraphics[width=0.8\\linewidth]{%s}\n' \
                   '    \\caption{%s}\n' \
                   '    \\label{%s}\n' \
                   '\\end{figure}%%\n' \
                   % (text, src, self.escape(title), text)
        return '\\begin{figure}[H]\n' \
               '    \\centering\n' \
               '    \\includegraphics[width=0.8\\linewidth]{%s}\n' \
               '    \\caption{%s}\n' \
               '\\end{figure}\n\n' \
               % (src, self.escape(title))

    def footnote_ref(self, key, index):
        raise NotImplementedError

    def footnote_item(self, key, text):
        raise NotImplementedError

    def footnotes(self, text):
        return text


def main():
    text = sys.stdin.read()

    front_matter = {}
    if text.startswith('---\n'):
        parts = text.split('\n---\n', 1)
        if len(parts) == 2:
            front_text = parts[0][4:]
            rest = parts[1]
            for line in front_text.split('\n'):
                if ':' in line:
                    key, _, val = line.partition(':')
                    front_matter[key.strip()] = val.strip()
            text = rest

    title = front_matter.get('title', '文档')
    author = front_matter.get('author', '')

    renderer = LaTeXRenderer()
    parser = mistune.Markdown(renderer=renderer)
    body = parser(text)

    print(r'''\documentclass[12pt,a4paper]{article}

\usepackage{ctex}
\usepackage[paper=a4paper,includefoot,margin=54pt]{geometry}
\usepackage[colorlinks,linkcolor=black,anchorcolor=black,citecolor=black,unicode]{hyperref}
\usepackage{float}
\usepackage{listings}
\usepackage[normalem]{ulem}
\usepackage{xcolor}
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}

\lstset{frame=single,breaklines=true,postbreak=\raisebox{0ex}[0ex][0ex]{\ensuremath{\hookrightarrow\space}}}

\renewcommand{\lstlistingname}{程序}
\renewcommand{\contentsname}{目录}
\renewcommand{\abstractname}{摘要}
\renewcommand{\refname}{参考文献}
\renewcommand{\indexname}{索引}
\renewcommand{\figurename}{图}
\renewcommand{\tablename}{表}
\renewcommand{\appendixname}{附录}

\begin{document}

\title{%s}
\author{%s}
\maketitle
\tableofcontents
\newpage

%s
\end{document}
''' % (title, author, body))

if __name__ == '__main__':
    main()