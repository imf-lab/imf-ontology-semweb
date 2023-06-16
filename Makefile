.INTERMEDIATE = %.temp

LUTRA = java -jar bin/lutra.jar -l out/ottr -L stottr -f -p out/.std-prefixes.ttl
RIOT = bin/apache-jena/bin/riot
SHACL = bin/apache-jena/bin/shacl v --text --shapes "http://shipshape.dyreriket.xyz/std-vocabulary-elements.ttl"

TTL-check = $(RIOT) --verbose --syntax=TTL --check --time $@
TTL-clean = rapper -i turtle -o turtle $@.temp > $@

code: \
	out/shacl/imf-terms-grammar.shacl.ttl \
	out/shacl/imf-model-grammar.shacl.ttl \
	out/shacl/imf-ontology-grammar.shacl.ttl \
	out/owl/imf-ontology.owl.ttl

all: 	code index.html


## ORG

.tangle: imf-language-v21.org
	emacs --batch --quick -l org -l ${HOME}/.emacs --eval "(org-babel-tangle-file \"$<\")"
	touch $@

index.html: imf-language-v21.org .tangle
	emacs --batch --quick -l ${HOME}/.emacs --visit $< -f org-html-export-to-html --kill

### Tangled files

out/.std-prefixes.ttl \
out/shacl/imf-terms-grammar.shacl.wottr.ttl \
out/shacl/imf-model-grammar.shacl.wottr.ttl \
out/shacl/imf-ontology-grammar.shacl.wottr.ttl \
out/owl/imf-ontology.owl.wottr.ttl: \
.tangle


### Lutra

%.ttl: %.wottr.ttl .tangle
	$(LUTRA) -I wottr -o $@.temp $<
	cat out/.std-prefixes.ttl >> $@.temp
	rapper -i turtle -o turtle $@.temp > $@
	rm $@.temp

### OWL


### QA

out.QA/%.ttl: out/%.ttl
	mkdir -p $(@D)
	$(SHACL) --data $< > $@
	if [ "Conforms" == `cat $@` ] ;then ; : else $(error non-conforming RDF file $<) ; fi



