#!/bin/bash

if [ -z "$oxygen_tool" ];then
    echo "Oxygen schema tool not found"
    echo "Please make sure you have a valid Oxygen license and call:"
    echo
    echo "export oxygen_tool=/path/to/Oxygen/schemaDocumentation.sh"
    echo
    echo "Switching to fallback schema documentation creator"
    echo
    ./schema_parser.py ../kiwi/schema/kiwi.rng \
        --output ../doc/source/schema.rst
else
    cat > ../doc/source/schema.rst <<- EOF
	.. _schema-docs:

	Schema Documentation 7.1
	========================

	.. raw:: html
	    :file: schema/schema.html
	EOF
    trang -I rnc -O xsd ../kiwi/schema/kiwi.rnc kiwi.xsd && \
        bash $oxygen_tool kiwi.xsd -cfg:schema_docs.conf
    rm -f kiwi.xsd xsi.xsd ../doc/source/schema/xsdDocHtml.css
fi
