flake8-function-definition
==========================

A `flake8 <http://flake8.readthedocs.org/en/latest/>`__ plugin that checks the
style of your function definitions.

Currently, only the Google suggested function definition style is supported by
this plugin. This assumes the following style from the Google Python Style
Guide::

    def foo(bar1, bar2, bar3, bar4, 
            bar5, bar6): 

1. ``def`` and ``foo`` and ``(`` are on the same line 
2. First argument is on same line as ``(`` 
3. Last argument is on same line as ``):`` 


Warnings
--------

This package adds 3 new flake8 warnings

-  ``FD101``: First argument must be on same line as the function definition.
-  ``FD102``: Function definition must end on same line as last argument. 
-  ``FD103``: def and function name must appear on the same line.


Contributing
------------

Pull requests are welcomed for new styles, additional features, and fixes.

If adding a new style, please create tests in the test/test_cases directory
which include an example for each error code and one "good" style test case.

For fixes and additional features, please modify existing tests as needed.
