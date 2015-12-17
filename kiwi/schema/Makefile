all: kiwi.rng kiwi.xsd

kiwi.rng: kiwi.rnc
	@echo "*** Converting KIWI RNC -> RNG..."
	trang -I rnc -O rng kiwi.rnc kiwi.rng

kiwi.xsd: kiwi.rnc
	@echo "*** Converting KIWI RNC -> XSD..."
	trang -I rnc -O xsd kiwi.rnc kiwi.xsd

clean:
	rm -f *.xsd *.rng
