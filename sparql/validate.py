import rdflib
import glob

g = rdflib.Graph()
#g.parse("...")

with open("prefixes.txt") as f:
    prefixes = f.read() 

files = glob.glob("*.sparql")
files.sort()
try:
    for filename in files:
        print(f"Parsing {filename}")
        with open(filename) as f:
            query = f.read() 
        query = prefixes + query
        qres = g.query(query)
        for row in qres:
            print(row)
            
except Exception as e:
    print(e)
    print(query)
    