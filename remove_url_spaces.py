#!/d/edemaine/bin/python

"""Remove whitespace from \\url{...} commands.

BibTeX has the annoying behavior that long lines are split using the TeX
comment character % for continuations.  Inside verbatim commands like \\url,
this introduces extra % characters in the final output.  There are several
workarounds to this problem.

One particularly attractive solution is to introduce extra spaces in the
argument to \\url.  This solution exploits that \\url operates in math mode,
and hence ignores any whitespace in the argument.

The trouble with this solution is that LaTeX2HTML's \\url command does not
ignore spaces.  At this point, however, preprocessing of the files ought to
be considered reasonable, and then you should use this script.  Simply give
an argument of the .bbl file with the \\url commands in it, or call
replace_file from another Python script.

Written by Erik Demaine on March 9, 2002.
"""

import os, re, string, sys

url_rec = re.compile (r"\\url\{[^{}]*\}", re.MULTILINE)

def remove_whitespace (urlspec):
  """Remove whitespace from a given string (such as '\\url{...}')."""
  return string.translate (urlspec, string.maketrans ("", ""), string.whitespace)

def fix_string (text):
  """Remove whitespace from \\url{...} commands in a given string."""
  return url_rec.sub (lambda match: remove_whitespace (match.group (0)), text)

def replace_file (filename):
  """Remove whitespace from contents of a file, and replace that file.

  The file is specifed by name.  The original is renamed with an extra ~
  suffix, and then the original name is written with the new contents.
  If the latter operation fails, the file is renamed back.
  """
  file = open (filename, "r")
  text = file.read ()
  file.close ()
  text = fix_string (text)
  os.rename (filename, filename + "~")
  try:
    file = open (filename, "w")
    file.write (text)
    file.close ()
  except IOError:
    os.rename (filename + "~", filename)
    raise

def replace_args ():
  """Calls replace_file with the script's arguments."""
  if len (sys.argv) <= 1:
    print """Usage: python remove_url_spaces.py filename.bbl ...
Removes whitespace from \\url{...} commands in the specified files.
Backups are stored in filename.bbl~."""
  else:
    map (replace_file, sys.argv[1:])

if __name__ == '__main__': replace_args ()
