RIOT = ../bin/apache-jena/bin/riot

%.jsonld.ttl: %.jsonld mimir-jsonld-context.jsonld
	$(RIOT) --output ttl $< > $@
