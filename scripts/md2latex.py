#!/usr/bin/env python3
# encoding=utf-8

import sys
import re
import mistune

# 强制输出 UTF-8
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout.detach())
sys.stdin = codecs.getreader('utf8')(sys.stdin.detach())

class LaTeXRenderer(mistune.Renderer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.replace = True

    # 代码块
    def block_code(self, code, lang=None):
        code = code.rstrip('\n')
        if lang and code:
            code = self.escape(code)
            return '\\begin{lstlisting}[language=%s]\n%s\n\\end{lstlisting}\n\n' % (lang, code)
        if lang:
            # 处理带文件名的格式，如 `python[filename.py]`
            lang, _, filename = lang[:-1].partition('[')
            return '\\lstinputlisting[language=%s, caption={%s}]{%s}\n\n' % (lang, self.escape(filename), filename)
        code = self.escape(code)
        return '\\begin{lstlisting}\n%s\n\\end{lstlisting}\n\n' % code

    # 引用块（自定义带背景色的盒子）
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

    # 标题（直接映射到 LaTeX 标题命令）
    def header(self, text, level, raw=None):
        levels = ['', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
        # level 从 1 开始
        if level <= len(levels)-1:
            cmd = levels[level]
        else:
            cmd = 'subparagraph'
        return '\\%s{%s}\n\n' % (cmd, text)

    # 水平线
    def hrule(self):
        return '\\hrule\n\n'

    # 列表
    def list(self, body, ordered=True):
        cmd = 'enumerate' if ordered else 'itemize'
        return '\\begin{%s}\n%s\\end{%s}\n\n' % (cmd, body, cmd)

    def list_item(self, text):
        return '\\item %s\n' % text

    # 段落
    def paragraph(self, text):
        return '%s\n\n' % text.strip(' ')

    # 表格（暂不支持，可根据需要扩展）
    def table(self, header, body):
        raise NotImplementedError

    def table_row(self, content):
        raise NotImplementedError

    def table_cell(self, content, **flags):
        raise NotImplementedError

    # 加粗 + 斜体
    def double_emphasis(self, text):
        return '\\textbf{\\emph{%s}}' % text

    # 斜体
    def emphasis(self, text):
        return '\\emph{%s}' % text

    # 行内代码
    def codespan(self, text):
        return '\\texttt{%s} ' % self.escape(text.rstrip())

    # 换行（Markdown 中的 \ 或两个空格）
    def linebreak(self):
        return '\\newline\n'

    # 删除线
    def strikethrough(self, text):
        # 使用 ulem 包的 \sout
        return '\\sout{%s}' % text

    # 普通文本（转义特殊字符）
    def text(self, text):
        return self.escape(text)

    # 转义 LaTeX 特殊字符（除数学模式外）
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
                # 需要转义的特殊字符
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

    # 自动链接
    def autolink(self, link, is_email=False):
        return self.escape(link)

    # 链接
    def link(self, link, title, text):
        return '\\href{%s}{%s}' % (self.escape(link), self.escape(text))

    # 图片（可选带标题）
    def image(self, src, title, text):
        # 如果有文本，作为 caption 和 label
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

    # 脚注（可选，暂不实现）
    def footnote_ref(self, key, index):
        raise NotImplementedError

    def footnote_item(self, key, text):
        raise NotImplementedError

    def footnotes(self, text):
        return text


def main():
    text = sys.stdin.read()

    # 尝试提取 front matter（简单支持 YAML 格式，无严格解析）
    front_matter = {}
    if text.startswith('---\n'):
        parts = text.split('\n---\n', 1)
        if len(parts) == 2:
            front_text = parts[0][4:]  # 去掉开头的 "---\n"
            rest = parts[1]
            # 简单解析 key: value
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

    # 输出完整的 LaTeX 文档
    print(r'''\documentclass[12pt,a4paper]{article}

\usepackage{ctex}
\usepackage[paper=a4paper,includefoot,margin=54pt]{geometry}
\usepackage[colorlinks,linkcolor=black,anchorcolor=black,citecolor=black,unicode]{hyperref}
\usepackage{float}
\usepackage{listings}
\usepackage[normalem]{ulem}   % 提供 \sout 删除线
\usepackage{xcolor}
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}

\lstset{frame=single,breaklines=true,postbreak=\raisebox{0ex}[0ex][0ex]{\ensuremath{\hookrightarrow\space}}}

% 自定义引用块样式（已由 block_quote 使用 tcolorbox）
% 这里不重复定义，避免冲突

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