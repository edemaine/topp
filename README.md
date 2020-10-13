# TOPP: The Open Problems Project

[TOPP.py](TOPP.py) is an [open-source](LICENSE) tool for converting TOPP-style
[problem specification files](Problems) into a website with those problems.
It uses [pandoc](https://pandoc.org/) to convert (limited) LaTeX into HTML,
including [KaTeX](https://katex.org/) for powerful LaTeX math rendering.

In particular, this repository builds
[the official TOPP problem list](https://topp.openproblem.net/)
via [Netlify](https://www.netlify.com/).
To build locally, install texlive and run `python2 TOPP.py`
to make an `html` directory.

## Submitting Updates

If you'd like to update any of the TOPP problems &mdash; for example,
to indicate progress from a recent paper or to correct a typo &mdash;
then please make a
[Github Pull Request](https://opensource.com/article/19/7/create-pull-request-github).
You probably want to:
1. edit a [problem specification file](Problems), and
2. add an entry to [the BibTeX file](topp.bib).

To correct a typo without adding a bib entry, you can go to the
[problem specification file](Problems) and click Github's Edit button.
This will create a fork with your change, which you can submit as a PR.

In the past, new problem submissions were created using
[this problem template](Problems/problem.template).
Feel free to use this template in your own project.
