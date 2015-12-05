all:
	${MAKE} -C startshell $@
	${MAKE} -C setctsid $@
	${MAKE} -C dcounter $@
	${MAKE} -C driveready $@
	${MAKE} -C utimer $@
	${MAKE} -C kversion $@
	${MAKE} -C isconsole $@

install:
	install -m 644 README ${PACKDOCVZ}/README.tools
	install -m 755 setctsid/setctsid ${TOOLSVZ}
	install -m 755 kversion/kversion ${TOOLSVZ}
	install -m 755 dcounter/dcounter ${TOOLSVZ}
	install -m 755 startshell/startshell ${TOOLSVZ}
	install -m 755 driveready/driveready ${TOOLSVZ}
	install -m 755 utimer/utimer ${TOOLSVZ}
	install -m 755 livestick/livestick ${TOOLSVZ}
	install -m 755 isconsole/isconsole ${TOOLSVZ}
	cp -a livestick/theme ${LIVESTICKVZ}

clean:
	${MAKE} -C dcounter $@
	${MAKE} -C setctsid $@
	${MAKE} -C startshell $@
	${MAKE} -C driveready $@
	${MAKE} -C utimer $@
	${MAKE} -C kversion $@
	${MAKE} -C isconsole $@
