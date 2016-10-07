#!/bin/bash

function all_attribute_getter {
    for match in $(grep -E '^    def get_' ../kiwi/xml_parse.py); do
        if [[ $match =~ ^get_ ]];then
            name=$(echo $match | cut -f1 -d'(')
            if [[ ! $name =~ _$ ]];then
                echo $name
            fi
        fi
    done | sort | uniq
}

for f in $(all_attribute_getter); do
    if ! find ../kiwi -name "*.py" | grep -v xml_parse.py | xargs grep -q $f
    then
        echo "--- $f"
    fi
done
