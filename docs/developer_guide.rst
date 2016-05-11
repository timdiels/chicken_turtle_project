Developer guide
===============

Project decisions
-----------------

Git stashing is not user-friendly and should not be relied upon. Stashing only
certain files or hunks can be done with ``git stash -p`` but that doesn't work
for new files. ``git add`` and ``git add -i`` are much friendlier. Other unfinished
changes can be left behind on a separate branch. (See also: 
`stack overflow thread <http://stackoverflow.com/questions/3040833/stash-only-one-file-out-of-multiple-files-that-have-changed-with-git>`_
and `this blog post <https://codingkilledthecat.wordpress.com/2012/04/27/git-stash-pop-considered-harmful/>`_)
By consequence we must allow committing only part of the working directory. We
can still require a clean directory before release however.

Warn on a poorly formatted project name (underscores, upper case) instead of
raising an error. The project may already have been submitted and the index 
may not allow renaming the package (although PyPI allows it through a support
ticket).

SIP based packages are not installable from PyPI and the SIP team hasn't fixed
this.  Writing a setuptools package for SIP is non-trivial. This means we must
use their build process (configure, make, make install). Eggs and wheels don't
allow installing files in system directories. SIP based packages stick close
enough to non-system directories in a venv. We could make a setup.py with
``zip_safe=False`` and put all files installed by ``make install`` in
`package_data`, then use `bdist_wheel` on it to create a binary
platform-dependent wheel. This is a bit more error-prone (e.g. a .so file
appearing in an unexpected place would break things) without much benefit as
these wheels probably can't be shared across machines. In order to support SIP
based packages, we install them without pip and reuse the dev venv in
pre-commits as to not incur the performance hit of waiting for a SIP package to
compile.

pytest-testmon is not compatible with pytest-xdist, --maxfail, --ff, --lf and
--cov to name a few. It sometimes misses changes that do cause test failures.
For these reasons, we default to using xdist instead of testmon. We may revisit
testmon once it supports xdist. You can still install and use --testmon
yourself, you probably shouldn't add --testmon to setup.cfg though as that would
allow for commits with failing tests.