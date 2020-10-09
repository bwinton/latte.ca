#
# ################ #
# refreshvcproj.py #
# ################ #
#
# Replaces the "Files" node in the specified Visual C++ project file with
# a new "Files" node that includes files in the specified directories
# (and its sub-directories).
#
# Originally written on January 15, 2010 at the Undergraduate Capstone Open
# Source Projects (UCOSP) Code Sprint for the Thunderbird team.
#
# HOW TO USE:
#  1. Create an empty Visual C++ project in Visual Studio. This script has
#     been tested on vcproj files for Visual Studio 2008 and 2010 Beta 2.
#  2. Run this script specifying the vcproj file created in step 1 as the
#     target vcproj file to refresh and a list of directories containing
#     the files you want to include in the projet.
#
# USAGE EXAMPLE:
#  $ python refreshvcproj.py --vcproj "d:\projects\thunderbird.vcproj"
#    --dir "d:\repos\mozilla\comm-central\mail"
#    --dir "d:\repos\mozilla\comm-central\mozilla"
#
# WARNING:
#  The "mozilla" directory is very big. Including all its subdirectories
#  and files will result in a project file that will take a relatively
#  long time to load.
#

import os
import sys
import xml.dom.minidom
from optparse import OptionParser

#
# Creates and returns an OptionParser instance configured with our options.
#
def initOptionParser():
    parser = OptionParser()

    parser.add_option("--vcproj", dest="vcproj", type="string")
    parser.add_option("--dir", dest="dirList", action="append", type="string")

    return parser

#
# Parses the command line and returns an object containing values for all of
# our options.
#
def parseArgs(parser):
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    # options: an object containing values for all of our options
    #
    # leftoverArgs: the list of positional arguments leftover after parsing
    #               options
    #
    # See http://docs.python.org/library/optparse.html
    (options, leftoverArgs) = parser.parse_args()

    return options

#
# Ensures that all required options are specified and validates the values for
# all specified options.
#
def validateOptions(options):
    # check for required options here. optparse doesn't give us much help at it
    if None == options.vcproj:
        print "--vcproj option is required."
        sys.exit(1)

    if None == options.dirList:
        print "Must specify at least one --dir option."
        sys.exit(1)

    # ensure the specified vcproj file exists
    options.vcproj = os.path.abspath(options.vcproj)
    if not os.path.isfile(options.vcproj):
        print "Cannot find vcproj file " + options.vcproj
        sys.exit(1)

    # ensure every specified source directory exist
    for dir in options.dirList:
        dirPath = os.path.abspath(dir)
        if not os.path.isdir(dirPath):
            print "Cannot find directory " + dirPath
            sys.exit(1)

###############################################################################

#
# Populates the specified "Filter" node with child "Filter" nodes representing
# sub-directories and child "File" nodes representing files in the specified
# directory.
#
# This function calls itself recursively.
#
def populateFilterNode(vcprojDoc, filterNode, dir):
    fileCount = 0

    for item in os.listdir(dir):
        itemPath = os.path.join(dir, item)

        # item can be a (sub-)directory or file
        if os.path.isdir(itemPath):
            # create a child "Filter" node for this sub-directory
            childFilterNode = vcprojDoc.createElement("Filter")
            childFilterNode.setAttribute("Name", item)

            # populate this node by calling ourself recursively
            childFileCount = populateFilterNode(vcprojDoc, childFilterNode, itemPath)

            # we only keep the non-empty child nodes
            if childFileCount > 0:
                filterNode.appendChild(childFilterNode)
            else:
                childFilterNode = None

            fileCount = fileCount + childFileCount

        elif os.path.isfile(itemPath):

            # create a child "File" node for this file
            childFileNode = vcprojDoc.createElement("File")

            # use the full path so the vcproj file can be moved anywhere on
            # disk
            childFileNode.setAttribute("RelativePath", itemPath)

            filterNode.appendChild(childFileNode)

            fileCount = fileCount + 1

    return fileCount

#
# Saves the document to the specified file.
#
def saveDoc(doc, filepath):
    file = open(filepath, "w")
    file.write(doc.toxml())
    file.close()

#
# Refreshes the "Files" node in the vcproj file specified by options.vcproj.
#
def refreshVCProj(options):
    # load the specified vcproj file
    vcprojDoc = xml.dom.minidom.parse(options.vcproj)

    # get the "Files" node. assume there's only one
    filesNode = vcprojDoc.getElementsByTagName("Files").item(0)

    # create a new "Files" node
    newFilesNode = vcprojDoc.createElement("Files")

    # populate the new "Files" node
    fileCount = 0
    for dir in options.dirList:
        filterNode = vcprojDoc.createElement("Filter")
        filterNode.setAttribute("Name", os.path.basename(dir))
        newFilesNode.appendChild(filterNode)
        # populate this "Filter" node
        fileCount = fileCount + populateFilterNode(vcprojDoc, filterNode, dir)

    # replace the old node with the new one
    filesNode.parentNode.replaceChild(newFilesNode, filesNode)

    # update the file on disk
    saveDoc(vcprojDoc, options.vcproj)

    print fileCount, "source files in project file", options.vcproj

###############################################################################

#
# This script's entry point
#    
def main():
    parser = initOptionParser()

    options = parseArgs(parser)
    validateOptions(options)

    refreshVCProj(options)

main()