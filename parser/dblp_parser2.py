'''
Created on Mar 27, 2016

@author: hugo
'''

import xml.sax
from mymysql.mymysql import MyMySQL
import config
import sys
import subprocess

total_lineno = None

class DBLPHandler(xml.sax.ContentHandler):
    def __init__(self, locator):
        self.loc = locator
        self.setDocumentLocator(self.loc)
        self.CurrentData = ""
        self.valid = False
        self.is_affil = False
        self.authors = set()
        self.affils = set()
        self.valid_count = 0 # num of homepage records
        self.progress = 0
        self.startDocument()
        self.file = None
        self.init()

    # Call when an element starts
    def startElement(self, tag, attr):
        self.CurrentTag = tag
        if tag == "www" and attr.has_key("key") \
                and "homepages" in attr["key"].split("/"):
            # www homepage tage
            self.valid = True
            self.valid_count += 1

        elif self.valid and tag == "note" and attr.has_key("type") \
                and attr["type"] == "affiliation":
            # affiliation
            self.is_affil = True

        if tag in ['article', 'inproceedings', 'proceedings', 'book', 'incollection',
                'phdthesis', 'mastersthesis', 'www']:
            self.progress += 1

    # Call when an elements ends
    def endElement(self, tag):
        if self.valid and tag == "www":
            self.valid = False # reset flag
            # pack data
            if self.affils:
                affil_names = list(self.affils)

                if self.authors:
                    author_name = list(self.authors)[0]
                    other_names = list(self.authors)[1:]

                    # write to db
                    print "author name: %s" % author_name
                    print "other names: %s" % other_names
                    print "affil names: %s" % affil_names
                    print
            self.authors.clear()
            self.affils.clear()

            if self.valid_count % 1000 == 0:
                print "%s homepages processed."%self.valid_count

        elif self.is_affil and tag == "note":
            self.is_affil = False

        # elif self.CurrentTag == "author":
            # print "Author:", self.author
        # elif self.CurrentTag == "note":
            # print "Note:", self.note
        # elif self.CurrentTag == "title":
            # print "Title:", self.title
        # elif self.CurrentTag == "url":
            # print "URL:", self.url

        self.CurrentTag = ""
        # print "progress: %.2f %%" % (self.get_progress()*100)

    # Call when a character is read
    def characters(self, content):
        if self.valid and self.CurrentTag == "author":
            self.authors.add(content.strip('\r\n').strip())
        if self.is_affil and self.CurrentTag == "note":
            self.affils.add(content.strip('\r\n').strip())
        # elif self.CurrentTag == "title":
            # self.title = content
        # elif self.CurrentTag == "url":
            # self.url = content

    def get_progress(self):
        return self.loc.getLineNumber()/float(total_lineno)

    def init(self):
        print "Initiating..."
        self.line_count = self.__count_lines()
        print "%s lines totally." % self.line_count


    def __count_lines(self):
        # Get total line number
        if self.file != None:
            for i, l in enumerate(self.file):
                pass
            self.file.seek(0)
            return i + 1

# get total line num of a file
def file_len(fname):
    p = subprocess.Popen(['wc', '-l', fname], stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    return int(result.strip().split()[0])

if __name__ == "__main__":
    try:
        in_file = sys.argv[1]
    except Exception, e:
        print e
        sys.exit()

    total_lineno = file_len(in_file)
    print "total line num of the file: %s" % total_lineno
    # create an XMLReader
    parser = xml.sax.make_parser()
    locator = xml.sax.expatreader.ExpatLocator( parser )
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    # override the default ContextHandler
    Handler = DBLPHandler(locator)
    parser.setContentHandler(Handler)
    parser.parse(in_file)
