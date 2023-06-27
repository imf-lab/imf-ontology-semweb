import sys, getopt
import rdflib
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import NamespaceManager, SH, RDFS, RDF, SKOS, OWL
from rdflib.collection import Collection

# input graph containing SHACL IMF types
iG = rdflib.Graph()

# output graph to contain RDF IMF model prototype
oG = rdflib.Graph()

nsPrototype = "http://example.org/prototype#"
nsIMF = "http://ns.imfid.org/imf#"
oG.bind("x", nsPrototype)
oG.bind("imf", nsIMF)

# list and function for storing constraint data as an editorialNote
shPs = [
  'name', 
  'description', 
  'class',
  'datatype',
  'minCount',
  'maxCount',
  'minExclusive',
  'minInclusive',
  'maxExclusive',
  'maxInclusive',
  'minLength',
  'maxLength',
  'pattern', 
  'flags'
]

# list of IMF classes that have associated Types
types = ['Block', 'Terminal', 'Attribute']

idN = 0

# function to generate new resources
def newId():
#return BNode()
  global idN
  idN += 1
  return URIRef(nsPrototype + "id-" + str(idN))


def copyConstaintAsNote(shapeId, protoId, noteHeading):
  note = "" 
  # single value properties
  for p in shPs:
    for o in iG.objects(shapeId, SH[p], None):
      note += "  - " + p + ": " + o + "\n"

  # list value property
  for o in iG.objects(shapeId, SH['in'], None):
    note += "  - in (values): " + ", ".join(Collection(iG, o)) + "\n"

  if note != "":
    oG.add((protoId, SKOS.editorialNote, Literal(noteHeading + ":\n" + note)))


def nodeShape(nodeId, protoId):

  for t in types:
    if (nodeId, RDF.type, URIRef(nsIMF + t + "Type")) in iG: # get the type class
      oG.add((protoId, RDF.type, URIRef(nsIMF + t))) # add the class

  for o in iG.objects(nodeId, SH.targetClass, None):
    oG.add((protoId, RDF.type, o))

  copyConstaintAsNote(nodeId, protoId, "SHACL Node shape description")

  for o in iG.objects(nodeId, SH.property, None):
    propShape(protoId, o)

def propShape(protoId, propId):

  path = iG.value(propId, SH.path, None)

  # if property shape has hasValue then add the value ...
  if (propId, SH.hasValue, None) in iG:
    for o in iG.objects(propId, SH.hasValue, None): 
      oG.add((protoId, path, o))

  # ... otherwise, for each minCount > 1, create a placeholder resource annotated with constraint info
  else:
    for n in range(max(1, int(iG.value(propId, SH.minCount, None, default=1)))):
      new = newId()
      oG.add((protoId, path, new))
      #copyConstaintAsNote(propId, new, "SHACL Property shape specification")
      if (propId, SH.node, None) in iG:
        nodeShape(iG.value(propId, SH.node, None), new)

def main(argv):
  inputfile = ''
  shapeIRI = ''
  outputfile = ''
  opts, args = getopt.getopt(argv,"hi:o:n:",["ifile=","ofile=","nodeShapeIRI="])

  for opt, arg in opts:
    if opt == '-h':
      print (sys.argv[0] + " -i <inputfile> -o <outputfile>")
      sys.exit()
    elif opt in ("-i", "--ifile"):
      inputfile = arg
    elif opt in ("-o", "--ofile"):
      outputfile = arg
    elif opt in ("-n", "--nodeShapeIRI"):
      shapeIRI = arg

  if inputfile == '' or outputfile == '':
    print("Error: missing options!")
    print("Usage: " + sys.argv[0] + " -i <inputfile> [-n <nodeShapeIRI>] -o <outputfile>")
    sys.exit()

  # Read input
  iG.parse(inputfile, format="ttl")

  if shapeIRI == '':
    for s in iG.subjects(RDF.type, SH.NodeShape):
      nodeShape(s, newId())
  else: 
    nodeShape(URIRef(shapeIRI), newId())

  oG.serialize(destination=outputfile)

if __name__ == "__main__":
   main(sys.argv[1:])
