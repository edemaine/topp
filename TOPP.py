#!/usr/bin/python2

from __future__ import nested_scopes
import fileinput, glob, os, re, shutil, string, sys, time, warnings
from UserDict import UserDict
from UserList import UserList
import remove_url_spaces

home_url = "http://cs.smith.edu/~orourke/TOPP/"
public_html = "/Users/orourke/public_html/TOPP/"
front_page_links_to_problems = 1
warning_file = open ("warnings", "w+")
latex2html = "/Users/edemaine/Packages/bin/latex2html"
if not os.path.exists (latex2html): latex2html = "latex2html"

##############################################################################

def main ():
  problems = read_problems (glob.glob ("Problems/P.[0-9][0-9][0-9][0-9][0-9][0-9]"))
  process_categories (problems)
  make_problems_latex (problems, "auto_problems.tex")
  make_numerical_problem_list (problems, "auto_numerical_problem_list.tex")
  make_categorized_problem_list (problems, "auto_categorized_problem_list.tex")
  make_category_list (problems, "auto_category_list.tex")
  os.system ("latex master")
  find_cites (problems, "master.aux")
  run ("bibtex master",
       "Warning", "Error", "couldn't open", "Repeated", "^ : ", "^I", "You're")
  remove_url_spaces.replace_file ("master.bbl")
  bibitems = grab_bibitems ("master.bbl")
  make_problems_latex (problems, "auto_problems.tex", bibitems)
  os.system ("latex master")
  run ("latex master", "(Citation|Reference).*undefined")
  os.system ("dvips -Ppdf -o master.ps master.dvi")
  os.system ("ps2pdf -dMaxSubsetPct=100 -dCompatibilityLevel=1.2 -dSubsetFonts=true -dEmbedAllFonts=true master.ps")
  run ("cp master.tex Welcome.tex")
  run ("cp master.aux Welcome.aux")
  footer = "The Open Problems Project - %s" % time.strftime ("%B %d, %Y")
  os.system ("%s -noreuse -split 4 -toc_depth 3 -link 0 -image_type gif -no_math -html_version 3.2,math,latin1,unicode -local_icons -accent_images=normalsize -nofootnode -address '%s' -init_file dot_latex2html-init -custom_titles Welcome.tex" % (latex2html, footer))
        ## -no_navigation
  run ("cp master.ps master.pdf Welcome/")
  run ("cp problem.template Welcome/")
  run ("chmod -R a+rX Welcome")
  run ("chgrp -R topp Welcome && chmod -R g+rwX Welcome")

  if len (sys.argv) > 1:
    print "Copying files into public_html..."
    #run ("cp -d -p Welcome/* %s" % public_html)
    copy_files ("Welcome/*", public_html)

  if warning_file.tell () > 0:
    print "*** Warnings from TOPP.py are in the file 'warnings'.  Please inspect. ***"

##############################################################################

class Problem (UserDict):
  def __init__ (self):
    UserDict.__init__ (self)
    self.fields = []  ## Ordered list of fields
  def cleanup_fields (self):
    ## Remove extreme blank lines.
    for key in self.keys ():
      if type (self[key]) == type ([]):
        while self[key] and self[key][0] == "":
          del self[key][0]
        while self[key] and self[key][-1] == "":
          del self[key][-1]
  def text_with_number_focus (self):
    return "Problem %d: %s" % (self['Number'], self['Problem'])
  def text_without_number_focus (self):
    return "%s (Problem~%d)" % (self['Problem'], self['Number'])

class Problems (UserDict):
  def category_list (self):
    ## Sort keys (categories) without regard to case.
    catlist = self.categories.keys ()
    catlist.sort (lambda x, y: cmp (x.lower (), y.lower ()))
    return catlist
  def problem_numbers (self):
    """Returns a sorted list of category numbers."""
    probnums = self.keys ()
    probnums.sort ()
    return probnums

class Categories (UserList):
  def __init__ (self, s):
    return UserList.__init__ (self, map (string.strip, string.join (s, " ").replace (",", ";").split (";")))
  def __str__ (self):
    return string.join (self, "; ")

##############################################################################

class TOPPWarning (UserWarning): pass

## Copy all warnings to warning_file.
def showwarning (*args, **dict):
  formatted = apply (warnings.formatwarning, args, dict)
  sys.stderr.write (formatted)
  warning_file.write (formatted)
warnings.showwarning = showwarning

def run (command, *keep):
  """Run the given command with os.system but with stderr copied to
  `warning_file`.

  If extra options are specified beyond the command, filter to include only
  lines with the specified regular expressions.

  """
  stdin, stdouterr = os.popen4 (command, bufsize = 1)
  stdin.close ()
  first = 1
  if not keep: keep = [""]
  while 1:
    line = stdouterr.readline ()
    if not line: break
    sys.stdout.write (line)
    for keeper in keep:
      if re.search (keeper, line):
        if first:
          warning_file.write ("--- Messages from running: %s\n" % command)
          first = 0
        warning_file.write (line)
        break
  stdouterr.close ()

def copy_files (src_spec, dest_dir):
  """Copy multiple files specified by glob pattern to target directory.

  Attempts to preserve mode and modification times, and produces one unique
  warning if this happens.

  Doesn't preserve links of any kind, but that seems safest in the context
  of LaTeX2HTML's hard links.

  """
  if not os.path.isdir (dest_dir):
    warnings.warn ("%r is not a directory; failing to copy %r there" %
                   (dest_dir, src_spec), TOPPWarning)
    return
  for src in glob.glob (src_spec):
    dest = os.path.join (dest_dir, os.path.basename (src))
    try:
      shutil.copyfile (src, dest)
      ## like shutil.copy but without preserving mode or anything
    except (IOError, OSError), e:
      warnings.warn ("Failed to copy %r to %r: %s" % (src, dest, e),
                     TOPPWarning)
    else:
      try:
        copygroup (src, dest)
        shutil.copymode (src, dest)
        shutil.copystat (src, dest)
      except (IOError, OSError), e:
        warnings.warn ("Unable to preserve some modes and/or modification "
                       "times while copying %r to %r" % (src_spec, dest_dir),
                       TOPPWarning)

def copygroup (src, dest):
  src_stat = os.stat (src)
  dest_stat = os.stat (dest)
  os.chown (dest, dest_stat.st_uid, src_stat.st_gid)

##############################################################################

problem_sep_re = r"^-+\s*$"
problem_sep_rec = re.compile (problem_sep_re)
field_re = r"^\* ([^:]*):\s*(.*)$"
field_rec = re.compile (field_re)
none_re = r"\<none\>"
none_rec = re.compile (none_re)

def read_problems (files):
  """Read one or more problems in TOPP problem format.

  Reads file(s) in problem format and outputs a dictionary of Problem's,
  indexed by problem number and secondarily indexed by field.
  A problem-file consists of one or more problem records, separated by
  a line of all dashes.  Each problem consists of a number of fields.
  Files no longer have to end with a line of all dashes to separate from the
  next file.

  Field begin:
        ^* field-name: field-value
  For certain fields (Number, Problem), the value is expected to be on that
  line.  For others, it may continue for an arbitrary number of lines.
  To suppress output for a field, use field-value of <none>. 
  For Categories field, categories are separated by ;'s (or ,'s).

  fname   : field name
  fvalue  : value of field on the field-name line
  pname   : Problem name
  pnumber : Problem number

  Note each problem is given a LaTeX label "Problem.N" where N is the
  problem number.  So there can be inter-problem references using \ref{}.
  """

  def end_problem ():
    problem.cleanup_fields ()
    ## Put problem in numeric index, assuming it has a number.
    if problem.has_key ('Number'):
      problems[problem['Number']] = problem
  def warn_where ():
    return "%s:%d" % (input.filename (), input.filelineno ())

  problems = Problems ()

  for file in files:
    problem = Problem ()
    fname = None
    input = fileinput.input (file)
    for line in input:
      line = line.rstrip ()  ## Trim off trailing whitespace, including newline
      if problem_sep_rec.match (line):
        end_problem ()
        problem = Problem ()
        fname = None
      elif field_rec.match (line):
        ## Beginning of new field
        match = field_rec.match (line)
        fname = match.group (1)
        fvalue = match.group (2) ## Note: leading spaces removed by pattern match.
        if none_rec.match (fvalue):
          pass  ## Ignore empty field.
        elif fname == 'Number':  ## Numeric single-line field
          problem[fname] = int (fvalue)
        elif fname == 'Problem':  ## Single-line field
          problem[fname] = fvalue
        else:
          if problem.has_key (fname):
            warnings.warn ("%s: Field %s occurs a second time in the same problem; second occurrence overwriting first" % (warn_where (), fname), TOPPWarning)
          else:
            problem.fields.append (fname)
          problem[fname] = [fvalue]
      else:
        if problem.has_key (fname):
          if type (problem[fname]) == type ([]):
            problem[fname].append (line)
          elif line:
            ## Nonblank lines after one-liner are ignored.
            warnings.warn ("%s: Field %s extends to multiple lines; only first line kept" % (warn_where (), fname), TOPPWarning)
        else:
          warnings.warn ("%s: Stray line outside of any field" % warn_where (), TOPPWarning)
    end_problem ()

  return problems

##############################################################################

def process_categories (problems):
  """Process 'Categories' field of all problems.

  Splits 'Categories' field according to separations by semicolons."""

  problems.categories = {}
  for problem in problems.values ():
    if not problem.has_key ('Categories'):
      ##continue
      warnings.warn ("Problem %d has no categories specified; listing under Miscellaneous" % problem['Number'], TOPPWarning)
      problem['Categories'] = 'Miscellaneous'
    problem['Categories'] = Categories (problem['Categories'])
    for category in problem['Categories']:
      if problems.categories.has_key (category):
        problems.categories[category].append (problem)
      else:
        problems.categories[category] = [problem]

##############################################################################

auto_disclaimer = "% DO NOT EDIT THIS FILE.  Auto-generated by TOPP.py.\n"

def make_problems_latex (problems, outname, bibitems = None):
  """Converts set of problems into a LaTeX file."""

  outfile = open (outname, "w")
  outfile.write (auto_disclaimer)
  if bibitems: ## Disable final \bibliography
    outfile.write ("%begin{latexonly}\n")
    outfile.write ("\\onebigbibfalse\n")
    outfile.write ("%end{latexonly}\n")
    outfile.write (bibitems['_commands'])

  for probnum in problems.problem_numbers ():
    problem = problems[probnum]
    text = problem.text_with_number_focus ()
#\\section*{\\htmladdnormallink{The Open Problem Project:}{%s}\\\\
#           \\label{Problem.%d}%s}
    outfile.write ("""

\\problem{%d}
%%begin{latexonly}
\\section*{\\label{Problem.%d}%s}
%%end{latexonly}
\\begin{htmlonly}
\\section*{\\label{Problem.%d}%s}
\\end{htmlonly}
\\refstepcounter{section}
\\begin{description}
""" % (probnum, probnum, text,
       #home_url,
       probnum, text))

    for field in problem.fields:
      if type (problem[field]) == type ([]):
        outfile.write ("\\item[%s] %s" %
                       (field, string.join (problem[field] + [""], "\n")))
      else:
        outfile.write ("\\item[%s] %s" % (field, str (problem[field])))

    outfile.write ("""
\\end{description}
""")

    if bibitems and problem.cites:
      outfile.write (bibitems['_begin'])
      for tag in problem.cites:
        if bibitems.has_key (tag):
          outfile.write (bibitems[tag])
        else:
          warnings.warn ("Problem %d cites unseen reference %s" % (probnum, tag), TOPPWarning)
      outfile.write (bibitems['_end'])

  outfile.close ()

##############################################################################

def make_numerical_problem_list (problems, outname):
  """Creates LaTeX file with list of all problems by number."""

  outfile = open (outname, "w")
  outfile.write (auto_disclaimer + """
\\section{\\label{numerical problem list}Numerical List of All Problems}
%%\\refstepcounter{section}

The following lists all problems sorted by number.
These numbers can be used for citations and correspond to the order in which
the problems were entered.

\\begin{itemize}
""")
  for probnum in problems.problem_numbers ():
    problem = problems[probnum]
    text = "Problem %d: %s" % (problem['Number'], problem['Problem'])
    outfile.write ("  \\item \\htmlref{%s}{Problem.%d}\n" %
                   (text, problem['Number']))
  outfile.write ("""
\\end{itemize}
""")
  outfile.close ()

##############################################################################

def make_categorized_problem_list (problems, outname):
  """Creates LaTeX file with list of categories and corresponding problems."""

  outfile = open (outname, "w")
  if front_page_links_to_problems:
    section = "\\subsection"
  else:
    section = "\\section"
  outfile.write (auto_disclaimer + """
%s{\\label{categorized problem list}Categorized List of All Problems}

Below, each category lists the problems that are classified under that category.
Note that each problem may be classified under several categories.

\\begin{description}
""" % section)
  catnum = 0
  for category in problems.category_list ():
    catnum += 1
    outfile.write ("""
\\item[\label{Category.%d}%s:]
%%begin{latexonly}
~
%%end{latexonly}
""" % (catnum, category))
    outfile.write ("\\begin{itemize}\n")
    problems_in_cat = problems.categories[category]
    problems_in_cat.sort (lambda x, y: cmp (x['Problem'], y['Problem']))
    for problem in problems_in_cat:
      text = problem.text_without_number_focus ()
      outfile.write ("  \\item \\htmlref{%s}{Problem.%d}\n" %
                     (text, problem['Number']))
      #outfile.write ("  \\item %s\n" % (problem.text_without_number_focus ()))
    outfile.write ("\\end{itemize}\n")
  outfile.write ("""
\\end{description}
""")
  outfile.close ()

##############################################################################

def make_category_list (problems, outname):
  """Creates LaTeX file with list of categories."""

  outfile = open (outname, "w")
  if front_page_links_to_problems: outfile.close (); return
  outfile.write (auto_disclaimer + """
\\html{%
\\subsection{\\label{category list}Categories}

\\begin{htmlonly}
To begin navigating through the open problems,
select a category of interest.  Alternatively, you may view
\\end{htmlonly}
%begin{latexonly}
The following lists the categories covered by the open problems.
See also
%end{latexonly}
\\hyperref{a list of all problems sorted by category}
          {Section }
          { for a list of all problems sorted by category}
          {categorized problem list}
or
\\hyperref{a list of all problems sorted numerically}
          {Section }
          { for a list of all problems sorted numerically}
          {numerical problem list}.

\\begin{itemize}
""")
  catnum = 0
  for category in problems.category_list ():
    catnum += 1
    outfile.write ("  \\item \htmlref{%s}{Category.%d}\n" % (category, catnum))
  outfile.write ("""
\\end{itemize}
}% \\html
""")
  outfile.close ()

##############################################################################

beginbiblio_re = r"^\\begin\{thebibliography\}"
beginbiblio_rec = re.compile (beginbiblio_re)
newcommand_re = r"^\\newcommand"
newcommand_rec = re.compile (newcommand_re)
endbiblio_re = r"^\\end\{thebibliography\}"
endbiblio_rec = re.compile (endbiblio_re)
bibitem_re = r"^\\bibitem.*\{([^\}]*)\}"
bibitem_rec = re.compile (bibitem_re)

def grab_bibitems (bblfile):
  """Finds \\bibitem statements in .bbl file.

  Returns a dictionary of strings indexed by the \\cite key.
  Each string is all the lines of the bibitem.
  There is also a special key '_begin' which contains the
  \\begin{thebibliography} line.  Ditto for '_end'.
  An additional entry '_commands' should be included just once."""

  bibitems = {'_begin': "", '_commands': "", '_end': ""}
  key = None
  for line in fileinput.input (bblfile):
    ## Store lines for later use.
    if beginbiblio_rec.match (line):
      bibitems['_begin'] += line
    elif newcommand_rec.match (line):
      bibitems['_commands'] += line
    elif endbiblio_rec.match (line):
      bibitems['_end'] += line
      break
    elif bibitem_rec.match (line):
      match = bibitem_rec.match (line)
      key = match.group (1)
      bibitems[key] = line
    elif key is not None:
      bibitems[key] += line
  return bibitems

##############################################################################

problem_marker_re = r"^% BeginProblem\{(\d+)\}"
problem_marker_rec = re.compile (problem_marker_re)
citation_re = r"^\\citation\{([^\}]*)\}"
citation_rec = re.compile (citation_re)

def find_cites (problems, auxfile):
  """Finds which problems cite which bibliographic references.

  Finds all \\citation commands in the given .aux file which has already been
  augmented by '% BeginProblem{123}' comments.  Sets the 'cites' entry of
  each problem to the list of references cited by that problem."""

  problem = None
  for line in fileinput.input (auxfile):
    if problem_marker_rec.match (line):
      match = problem_marker_rec.match (line)
      problem = problems[int (match.group (1))]
      problem.cites = []
    elif citation_rec.match (line):
      match = citation_rec.match (line)
      if problem is not None:
        problem.cites.append (match.group (1))
      else:
        warnings.warn ("Citation %s used before a problem began; potentially dangerous" % match.group (1), TOPPWarning)
  for problem in problems.values ():
    ## Sort and remove duplicate citations
    problem.cites.sort ()
    for i in range (len (problem.cites) - 1, 0, -1):
      if problem.cites[i] == problem.cites[i-1]:
        del problem.cites[i]

##############################################################################

if __name__ == '__main__':
  main ()
