.INTERMEDIATE = %.temp


RIOT = bin/apache-jena/bin/riot
SHACL = bin/apache-jena/bin/shacl v --text

TTL-check = $(RIOT) --verbose --syntax=TTL --check --time $@
TTL-clean = rapper -i turtle -o turtle $@.temp > $@

code: \
	out/shacl/imf-terms-grammar.shacl.ttl \
	out/shacl/imf-model-grammar.shacl.ttl \
	out/shacl/imf-ontology-grammar.shacl.ttl \
	out/shacl/imf-types-grammar.shacl.ttl \
	out/owl/imf-ontology.owl.ttl

all: 	code index.html


## ORG

.tangle: main.org
	emacs --batch --quick -l org -l ${HOME}/.emacs --eval "(org-babel-tangle-file \"$<\")"
	touch $@

index.html: main.org .tangle
	emacs --batch --quick -l ${HOME}/.emacs --visit $< -f org-html-export-to-html --kill

## OTTR

LUTRA = java -jar bin/lutra.jar -l ottr -L stottr -f -p out/.std-prefixes.ttl
OTTR-lib = $(wildcard ottr/*)

test: $(OTTR-lib)
	echo $(OTTR-lib)

### Tangled files



out/.std-prefixes.ttl \
out/ottr/imf-ontology/aspects.stottr \
out/ottr/imf-ontology/attributes.stottr \
out/ottr/imf-types-shacl.stottr \
XXXout/owl/imf-ontology.owl.wottr.ttl \
out/py/imftype-shacl2owl.py \
out/py/imftype-shacl2rdf.py \
out/shacl/imf-model-grammar.shacl.ttl \
out/shacl/imf-ontology-grammar.shacl.ttl \
out/shacl/imf-terms-grammar.shacl.ttl \
out/shacl/imf-types-grammar.shacl.ttl : \
.tangle


### Lutra

owl/imf-ontology.owl.ttl: owl/imf-ontology.owl.wottr.ttl $(OTTR-lib)
	$(LUTRA) -I wottr -o $@.temp $<
	cat out/.std-prefixes.ttl >> $@.temp
	rapper -i turtle -o turtle $@.temp > $@
	rm $@.temp

owl/imf-ontology.owl.ttl-val.txt: owl/imf-ontology.owl.ttl
	echo "* http://shipshape.dyreriket.xyz/std-vocabulary-elements.ttl" > $@
	$(SHACL) --shapes "http://shipshape.dyreriket.xyz/std-vocabulary-elements.ttl" --data $^ >> $@
	echo "\n\n* shacl/imf-ontology-grammar.shacl.ttl" >> $@
	$(SHACL) --shapes shacl/imf-ontology-grammar.shacl.ttl --data $^ >> $@

### tabOTTR

%.xlsx.ttl: %.xlsx #.tangle
	$(LUTRA) -I tabottr $< | rapper - -i turtle -o turtle -I 'http://base.com#' > $@

# for IMF manual

imf-ontology.tex: ../py-imf-tools/ont2latex.py out/owl/imf-ontology.owl.ttl out/shacl/imf-model-grammar.shacl.ttl
	python3 $^ $@
