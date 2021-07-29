# versa.pipeline
'''
Framework for expressing transforms from one pattern of Versa links to another
Useful for iterative processing or vocabulary mapping

Concept is similar to XProc (http://en.wikipedia.org/wiki/XProc). You define
the overall transform in terms of transform steps or stages, implemented as
Python functions. Each function can have inputs, which might be simple Versa
scalars or even functions in themselves. The outputs are Versa scalars.

There is shared context (`versa.context`) across the steps.
This includes a resource which is considered the origin for purposes
of linking, an input Versa model considered to be an overall input to the transform
and an output Versa model considered to be an overall output.

You can use the `transform` function to take a raw record in any format,
define an edge stage transform to convert the raw data to an initial Versa context,
and then iterate through the other defined transform stages.
'''

from .main import *
from .link_materialize_actions import *
from .other_actions import *
