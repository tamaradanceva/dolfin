#!/usr/bin/env python
"""Simple functions to update the docstrings.i file for the Python interface
from the intermediate representation of the documentation which is extracted
from the C++ source code of DOLFIN.

This script assumes that all functions and classes lives in the dolfin namespace.
"""

__author__ = "Kristian B. Oelgaard (k.b.oelgaard@gmail.com)"
__date__ = "2010-08-19"
__copyright__ = "Copyright (C) 2010 Kristian B. Oelgaard"
__license__  = "GNU LGPL Version 2.1"

# Last changed: 2010-10-14

# Modified by Johan Hake, 2010.

import os, shutil, types, sys

# Set top DOLFIN directory.
dolfin_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),\
                                              os.pardir, os.pardir))
# Add path to dolfin_utils and import the documentation extractor.
doc_dir = os.path.abspath(os.path.join(dolfin_dir, "site-packages"))
sys.path.append(doc_dir)
from dolfin_utils.documentation import extract_doc_representation, indent, add_links
from codeexamples import codesnippets

if os.path.isfile("docstrings.i"):
    os.remove("docstrings.i")
output_file = open("docstrings.i", "a")
docstring = '%%feature("docstring")  %s "\n%s\n";\n\n'

def get_function_name(signature):
    "Extract function name from signature."
    words = signature.split("(")[0].split()
    # Special handling of operator since Swig needs 'operator double', not just
    # 'double', which is different from _normal_ operators like 'operator='
    if len(words) > 1 and words[-2] == "operator":
        return " ".join(words[-2:])
    return words[-1]

def group_overloaded_functions(docs):
    """Group functions with same name, but different signature.
    Assuming that overloaded functions in the dolfin namespace are defined
    in the same header file."""

    new_docs = []
    for (classname, parent, comment, function_documentation) in docs:
        func_doc = {}
        order = []
#        print "cls: ", classname
        # Iterate over class functions
        for (signature, comm) in function_documentation:
            # No need to put empty docstrings in the docstrings.i file!
            if comm is None:
                continue
#            print "sig: ", signature
            name = get_function_name(signature)
            if not name in order:
                order.append(name)
#            print "name: '%s'" % name
            if not name in func_doc:
                func_doc[name] = [(signature, comm)]
            else:
                func_doc[name].append((signature, comm))
        new_docs.append((classname, parent, comment, func_doc, order))

    return new_docs

def replace_example(text, classname, signature):
    """Replace the C++ example code with the Python equivalent.
    Currently we can only handle one block/section of example code per function.
    """
    # Check if we need to manipulate comment.
    if not "*Example*" in text:
        return text

#    print "'%s'" % signature
    return text

def modify_doc(text, classnames, classname, signature):
    "Add links, translate C++ to Python and change return types."

    # Add links
    text = add_links(text, classnames, ":py:class:")

    # Escape '"' otherwise will SWIG complain
    text = text.replace('\"',r'\"')

    text = replace_example(text, classname, signature)
    # TODO: KBO: Still need to translate return types.
    return text

def get_args(signature):
    "Get argument names (for Python) from signature."
#    print "sig: ", signature
    arg_string = signature.split("(")[-1].split(")")[0]
#    print "arg_string: '%s'" % arg_string
    args = []
    if arg_string:
        args = [a.split()[-1] for a in arg_string.split(",")]
#    print "args: '%s'" % args
    return args


def write_docstrings(module, header, docs, classnames):
    """Write docstrings from a header file."""

    output_file.write("// Documentation extracted from: (module=%s, header=%s)\n" % (module, header))

    documentation = group_overloaded_functions(docs)
    for (classname, parent, comment, func_docs, order) in documentation:
        # Create class documentation (if any) and write.
        if classname is not None and comment is not None:
            cls_doc = modify_doc(comment, classnames, classname, classname)
            output_file.write(docstring % ("dolfin::%s" % classname, cls_doc))
        # Handle functions in the correct order (according to definition in the
        # header file).
        for name in order:
            func_name = "dolfin::%s::%s" % (classname, name)
            if classname is None:
                func_name = "dolfin::%s" % name

            functions = func_docs[name]
            if not functions:
                continue
            # We've got overloaded functions.
            if len(functions) > 1:
                func_doc = "**Overloaded versions**"
                for signature, doc in functions:
                    args = get_args(signature)
                    doc = "\n\n* %s\ **(%s)**\n\n" % (name, ", ".join(args)) +\
                          indent(doc, 2)
                    func_doc += modify_doc(doc, classnames, classname, signature)
                output_file.write(docstring % (func_name, func_doc))
            # Single function
            else:
                # Get function (only one)
                signature, func_doc = functions[0]
                func_doc = modify_doc(func_doc, classnames, classname, signature)
                output_file.write(docstring % (func_name, func_doc))

def generate_docstrings():

    output_file.write("// Autogenerated docstrings file, extracted from the DOLFIN source C++ files.\n\n")

    # Get top DOLFIN directory.
    dolfin_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),\
                                              os.pardir, os.pardir))

    documentation, classnames = extract_doc_representation(dolfin_dir)
    print "Generating docstrings.i from intermediate representation module..."
    for module in documentation:
##        if module != "common":
#        if module != "mesh":
#        if module != "function":
#            continue
        print " "*2 + module
        for header, docs in documentation[module]:
##            if header != "timing.h":
#            if header != "Mesh.h":
#            if header != "Vertex.h":
#                continue
            print " "*4 + header
            write_docstrings(module, header, docs, classnames)

    output_file.close()

if __name__ == "__main__":
    generate_docstrings()

