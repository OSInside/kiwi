#/.../
# Copyright (c) 2001 SuSE GmbH Nuernberg, Germany. All rights reserved.
# Author: Marcus Schaefer <ms@suse.de>, 2001
#
# Makefile for KIWI po file generation
#
KIWILOCVZ = /usr/share/kiwi/locale
LC        = LC_MESSAGES

all:
	./.locale
	for i in `ls -1 .`; do \
		if [ -d ./$$i ];then \
			if [ ! "$$i" = "kiwi-help" ] && [ ! "$$i" = "kiwi-template" ];then \
				( cd ./$$i/${LC}  && msgfmt -o kiwi.mo kiwi.po ) ;\
			fi \
		fi \
	done


install:
	for i in `ls -1 .`; do \
		if [ -d ./$$i ];then \
		if [ ! "$$i" = "kiwi-help" ] && [ ! "$$i" = "kiwi-template" ];then \
		install -d -m 755 ${KIWILOCVZ}/$$i/${LC} ;\
		test -e ./$$i/${LC}/kiwi.mo && \
			install -m 644 ./$$i/${LC}/kiwi.mo ${KIWILOCVZ}/$$i/${LC} || true ;\
		fi \
		fi \
	done

status:
	./.fuzzy

clean:
	find -name kiwi.*.po | xargs rm -f
	find -name kiwi.po.old | xargs rm -f
	find -name kiwi.mo | xargs rm -f
