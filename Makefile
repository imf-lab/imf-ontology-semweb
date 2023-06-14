.INTERMEDIATE = %.temp

LUTRA = java -jar bin/lutra.jar -l out/ottr -L stottr -f -p out/.std-prefixes.ttl
RIOT = bin/apache-jena/bin/riot
SHACL = bin/apache-jena/bin/shacl v --text --shapes "http://shipshape.dyreriket.xyz/std-vocabulary-elements.ttl"

TTL-check = $(RIOT) --verbose --syntax=TTL --check --time $@
TTL-clean = rapper -i turtle -o turtle $@.temp > $@

code: \
	out/owl/imf.owl.ttl \
	out/shacl/imf.shacl.ttl \

all: 	code index.html


## ORG

.org-tangle-%: %
	emacs --batch --quick -l org -l ${HOME}/.emacs --eval "(org-babel-tangle-file \"$<\")"
	touch $@

index.html: imf-language-v21.org .org-tangle-imf-language-v21.org
	emacs --batch --quick -l ${HOME}/.emacs --visit $< -f org-html-export-to-html --kill

### Tangled files

out/.std-prefixes.ttl \
out/shacl/imf.shacl.wottr.ttl \
out/owl/imf.owl.wottr.ttl: \
.org-tangle-imf-language-v21.org

### Lutra

%.ttl: %.wottr.ttl
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



