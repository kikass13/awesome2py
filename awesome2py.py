from markdown import markdownFromFile, markdown
from bs4 import BeautifulSoup, element, Tag
from pprint import pprint
import json 

import sys

### amount of spaces (factor) for sub entrys, default = 2
SUB_LIST_SPACING = 2

class AwesomeListRubric(object):
    def __init__(self, key, rubricEntries):
        super(AwesomeListRubric, self).__init__()
        self.key = key
        self.entries = []
        #pprint(rubricEntries)
        for entry in rubricEntries:
            new = AwesomeListEntry(entry)
            if new:
                self.entries.append(new)

    def __str__(self):
        s = "%s\n" % (self.key)
        for e in self.entries:
            s += "%s" % (e)
        return s
    def __repr__(self):
        return str(self)
    def toDict(self):
        return {self.key : [e.toDict() for e in self.entries]}

class AwesomeListEntry(object):
    def __init__(self, entry, depth=0):
        super(AwesomeListEntry, self).__init__()
        me, children = entry

        self.depth = depth
        htmldata = me.find("a", href=True).extract()
        self.html = str(htmldata)
        self.url = htmldata["href"].strip()
        self.name = htmldata.get_text().strip()
        self.text = me.get_text().strip()

        self.children = []
        for subentry in children:
            self.children.append(AwesomeListEntry(subentry, depth=self.depth+1))

    def __str__(self):
        s = self.depth * SUB_LIST_SPACING * " " + " - %s %s [%s]\n" % (self.name, self.text, self.url)
        for child in self.children:
            s += str(child)
        return s
    def __repr__(self):
        return str(self)
    
    def toDict(self):
        d = { 
            "name" : self.name, "url": self.url, "text" : self.text, "html": self.html, "depth": self.depth, 
            "children": [c.toDict() for c in self.children]
        }
        return d

class AwesomeList(object):
    def __init__(self, path):
        super().__init__()
        self.rubrics = []
        soup = self.convertFromHtml(path)
        #print(soup)
        contents, d = self.generateDict(soup)
        self.createStructure(contents, d)
    def convertFromHtml(self, path):
        html = markdown(open(path).read())
        soup = BeautifulSoup(html, features='html.parser')
        #print(soup.prettify())
        return soup
    def findOutIfSubListsAreUsed(self, soup):
        toc = soup.find("h3")
        return toc != None

    def findContents(self, soup):
        d = {}
        ### find content h2
        while True:
            toc = soup.find("h2")
            if toc and toc.get_text() == "Contents":
                toc.extract() ## extract will consume the item
                aList = self.findList(soup)
                if aList:
                    for item in self.findListItems(aList):
                        ali = AwesomeListEntry(item)
                        d[ali.name] = ali.html
                break
        ### remove "Contents" from contents dict
        if "Contens" in d:
            del d["Contents"]
        return d

    def generateDict(self, soup):
        ### we ll specifically fetch the contents entry        
        contents = self.findContents(soup)
        ### find out if sub list entries were used here [pre consume] ... (experimental)
        subListsAreUsed = self.findOutIfSubListsAreUsed(soup)
        ### crawl though all categories and extract information
        ### ...
        ### if sublists are used, we have now parsed the h2 main list entries
        ### as well as the h3 sub list entries ... which results in every entry being 
        d = self.findLists(soup, subListsAreUsed)
        return contents, d

    def createStructure(self, contents, d):
        #children = self.findListItems(contents, ignoreSubLists=True) 
        for c,v in contents.items():
            rubricKey = c
            rubricEntries = d.get(rubricKey, None)
            if rubricEntries:
                entries = self.findListItems(rubricEntries)
                self.rubrics.append(AwesomeListRubric(rubricKey, entries))

    def toDict(self):
        d = {}
        for r in self.rubrics:
            d.update(r.toDict())
        return d
    ########################################################
    def findLists(self, soup, subListsAreUsed = False):
        d = {}
        while True:
            ### if there is no major content list defind anymore, we try parsing sub lists
            if subListsAreUsed:
                toc = soup.find("h3")
            else:
                toc = soup.find("h2")
            ### start analyzing whatever list was found
            if toc:
                toc.extract() ## extract will consume the item
                aList = self.findList(soup)
                if aList:
                    d[toc.get_text()] = aList
            else:
                break
        return d
    def findList(self, parent):
        ul = parent.find("ul")
        if ul:
            ul.extract()
        return ul

    def findListItems(self, parent,  ignoreSubLists=False, depth=0):
        children = parent.findChildren("li", recursive=False)
        if ignoreSubLists == False:
            tree = []
            tree.extend([(child, []) for child in children])
            for i, data in enumerate(tree):
                child, subChilds = data
                ### does this item has subitems?
                subList = self.findList(child)
                if subList:
                    ### sublist found ... now add it
                    ###recursion
                    recursiveSubLists = self.findListItems(subList, depth=depth+2)
                    tree[i] = (child, recursiveSubLists)
                #print(" " * depth + "+" +str(tree[i]).replace("\n", ""))
            ### overwrite the normal children list with the special tupled treelist containing subs and stuff
            children = tree
        return children
    
    def __str__(self):
        s = ""
        for e in self.rubrics:
            s += "%s" % (e)
        return s
    def __repr__(self):
        return str(self)


def main():
    path = "samples/awesomeListSample.md"
    if(len(sys.argv) > 1):
        path = sys.argv[1]

    alc = AwesomeList(path)
    #print("===============================================")
    #print(alc)
    total = 0
    ### simple human readable output
    with open("output.txt", "w") as f:
        for r in alc.rubrics:
            f.write(str(r))
            print(r)
    ### semi simple output
    # for r in alc.rubrics:
    #     #print("%s [%s]" % (r.key, len(r.entries)))
    #     total += len(r.entries)
    #     print(r.key)
    #     for e in r.entries:
    #       print(e)
    ### tedious output
    # for r in alc.rubrics:
    #     print("=================================")
    #     print(r.key)
    #     print("=================================")
    #     for e in r.entries:
    #         print(e.name)
    #         ### this should be recursive when done properly
    #         for child in e.children:
    #             print("  "  + child.name)  
    #     print("")          
    ### dict conversion
    # for k, v in alc.toDict().items():
    #     print(k)
    #     for e in v:
    #         print(e)
    #     print("#########################################")
    ### dict to json
    j = json.dumps(alc.toDict(), indent=2) 
    with open("json.txt", "w") as f:
        f.write(j)
    #print("===============================================")
    #print("Done parsing '%s' entries." % total)

if __name__ == "__main__":
    main()
