CFGDIR=/var/lib/adminkit

all:
	cd docs; make html

test:
	./tests/tests.sh

check:
	pylint --disable-msg=C0103,C0301,W0603 -f parseable adminkit

install:
	mkdir -p $(DESTDIR)/usr/bin $(DESTDIR)/usr/share/adminkit \
	$(DESTDIR)$(CFGDIR)/roles $(DESTDIR)$(CFGDIR)/files \
	$(DESTDIR)$(CFGDIR)/once \
	$(DESTDIR)$(CFGDIR)/adminkit.conf.d
	install adminkit $(DESTDIR)/usr/bin/
	install -m 644 debian.py mandriva.py ubuntu.py adminkit.py $(DESTDIR)/usr/share/adminkit/
	install -m 755 update-adminkit.conf $(DESTDIR)/usr/share/adminkit/

clean:
	rm -f *~ *.pyc
	cd docs; make clean
