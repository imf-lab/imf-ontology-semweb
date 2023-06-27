import sys, getopt
import rdflib
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import NamespaceManager, XSD, SH, RDFS, RDF, SKOS, OWL
from rdflib.collection import Collection

def newId():
  return BNode()

# input graph containing SHACL IMF types
iG = rdflib.Graph()


nsIMF = "http://ns.imfid.org/imf#"

# IMF vocabulary
ontIMF = rdflib.Graph()
iriIMF = "https://imf-lab.gitlab.io/imf-ontology/out/owl/imf-ontology.owl.ttl"
ontIMF.parse(iriIMF, format="ttl")
ontIMF.bind("imf", nsIMF)

# output graph
oG = rdflib.Graph()
oG.bind("imf", nsIMF)

# list of IMF classes that have associated Types
types = ['Block', 'Terminal', 'Attribute']

# map of type classes to IMF classes
mapC = { URIRef(nsIMF + t + "Type"): URIRef(nsIMF + t) for t in types }

# map SHACL to OWL
map = {
  SH.name: RDFS.label,
  SH.description: RDFS.comment,
  SH.path: OWL.onProperty,
  SH.hasValue: OWL.hasValue,
  SH.minCount: OWL.minQualifiedCardinality,
  SH.maxCount: OWL.maxQualifiedCardinality,
  SH.datatype: OWL.onDataRange,
  SH.minExclusive: XSD.minExclusive,
  SH.minInclusive: XSD.minInclusive,
  SH.maxExclusive: XSD.maxExclusive,
  SH.maxInclusive: XSD.maxInclusive,
  SH.minLength: XSD.minLength,
  SH.maxLength: XSD.maxLength ,
  SH.pattern: XSD.pattern
  #SH.flags:
}

# selection of properties
mapP = [
  SH.name,
  SH.description,
  SH.path,
  SH.hasValue,
  SH.minCount,
  SH.maxCount
]

# selection of facets
mapF = [
  SH.minExclusive,
  SH.minInclusive,
  SH.maxExclusive,
  SH.maxInclusive,
  SH.minLength,
  SH.maxLength,
  SH.pattern
  #SH.flags
]

def copyObjects(sourceS, sourceP, targetS, targetP, defaultO=None):
  if (sourceS, sourceP, None) in iG:
    for o in iG.objects(sourceS, sourceP, None):
      oG.add((targetS, targetP, o))
  elif defaultO != None:
    oG.add((targetS, targetP, defaultO))

# add a list to output graph as RDF list
def addCollection(targetS, targetP, collection):
  size = len(collection)
  head = newId()
  oG.add((targetS, targetP, head))
  for i in range(size):
    newHead = newId()
    oG.add((head, RDF.first, collection[i]))
    if (i == size-1):
      oG.add((head, RDF.rest, RDF.nil))
    else:
      oG.add((head, RDF.rest, newHead))
      head = newHead

### Create a class of the node shape, adding propertyShapes as class restrictions.
def nodeShape(nShape):

  # get IRI
  classId = iG.value(nShape, SH.targetClass, None)
  oG.add((classId, RDF.type, OWL.Class))

  # translate classification
  superclasses = []
  for key in mapC:
    if (nShape, RDF.type, key) in iG:
      oG.add((classId, RDFS.subClassOf, mapC[key]))
      superclasses.append(mapC[key])

  # translate SH properties to OWL
  for key in mapP:
    copyObjects(nShape, key, classId, map[key])

  # collect class restriction resources for each SH property shape:
  restrictions = []

  for pShape in iG.objects(nShape, SH.property, None):
    rstr = newId()
    oG.add((classId, RDFS.subClassOf, rstr))
    if propShape(rstr, pShape): # collect only non-vacuous restrictions
      restrictions.append(rstr)

  if len(restrictions) > 1:
    restrictions.extend(superclasses)
    _equivs = newId()
    oG.add((_equivs, RDFS.subClassOf, classId))
    oG.add((_equivs, RDF.type, OWL.Class))
    addCollection(_equivs, OWL.intersectionOf, restrictions)

### Create class restrictions of property shape.
def propShape(rstr, pShape):

  oG.add((rstr, RDF.type, OWL.Restriction))

  # translate SH properties to OWL
  for key in mapP:
    copyObjects(pShape, key, rstr, map[key])

  # add target class/datatype if not a hasValue
  if (rstr, OWL.hasValue, None) not in oG:

    # add default min card if not set
    if (rstr, OWL.minQualifiedCardinality, None) not in oG:
      oG.add((rstr, OWL.minQualifiedCardinality, Literal(0, datatype=XSD.nonNegativeInteger)))

    # is path a data property or object property; let's ask the IMF ontology.
    property = iG.value(pShape, SH.path, None)
    if (property, RDF.type, OWL.ObjectProperty) in ontIMF:
      targetProperty = OWL.onClass
      targetClassifier = OWL.Class
    else:
      targetProperty = OWL.onDataRange
      targetClassifier = RDFS.Datatype

    # SH.in, copy list
    for o in iG.objects(pShape, SH['in']):
      _oneOf = newId()
      oG.add((rstr, targetProperty, _oneOf))
      oG.add((_oneOf, RDF.type, targetClassifier))
      addCollection(_oneOf, OWL.oneOf, Collection(iG, o))


    if targetProperty == OWL.onClass: # ObjectProperty

      # add SH.node -> SH.targetClasses as OWL.onClass
      for nShape in iG.objects(pShape, SH.node):
        for targetClass in iG.objects(nShape, SH.targetClass):
          oG.add((rstr, OWL.onClass, targetClass))

      if (rstr, OWL.onClass, None) not in oG:
        oG.add((rstr, OWL.onClass, OWL.Thing))

    else: # not ObjectProperty

      # get datatype, defaulting to RDFS.Literal
      datatype = iG.value(pShape, SH.datatype, None, RDFS.Literal)

      # collect any facets
      facetTriples = []
      for key in mapF:
        if (pShape, key, None) in iG:
          facetTriples.append((newId(), map[key], iG.value(pShape, key, None)))
      
      # create a wrapping datatype for the facets
      if len(facetTriples) > 0:
        _datatype = newId()
        facetS = [t[0] for t in facetTriples]
        oG.add((rstr, OWL.onDataRange, _datatype))
        oG.add((_datatype, RDF.type, RDFS.Datatype))
        oG.add((_datatype, OWL.onDatatype, datatype))
        for t in facetTriples:
          oG.add(t)
        addCollection(_datatype, OWL.withRestrictions, facetS)
     
      # if no facets, add datatype 
      else:
        oG.add((rstr, map[SH.datatype], datatype))

  # return True if include in intersectionOf axioms on class, avoiding vacuous statements
  return (rstr, OWL.hasValue, None) in oG or oG.value(rstr, OWL.minQualifiedCardinality, None, Literal(0)) > Literal(0)

def main(argv):
  inputfile = ''
  outputfile = ''
  opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])

  for opt, arg in opts:
    if opt == '-h':
      print (sys.argv[0] + " -i <inputfile> -o <outputfile>")
      sys.exit()
    elif opt in ("-i", "--ifile"):
      inputfile = arg
    elif opt in ("-o", "--ofile"):
      outputfile = arg

  if inputfile == '' or outputfile == '':
    print("Error: missing options!")
    print("Usage: " + sys.argv[0] + " -i <inputfile> -o <outputfile>")
    sys.exit()

  # Read input
  iG.parse(inputfile, format="ttl")

  # Translate all node shapes
  for x in iG.subjects(RDF.type, SH.NodeShape):
    nodeShape(x)

  # Add ontology import
  _ont = newId()
  oG.add((_ont, RDF.type, OWL.Ontology))
  oG.add((_ont, OWL.imports, URIRef(iriIMF)))
  oG.serialize(destination=outputfile)

if __name__ == "__main__":
   main(sys.argv[1:])
