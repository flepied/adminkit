CFGDIR=/var/lib/adminkit

all:
	cd docs; make html

test:
	./tests/tests.sh

install:
	mkdir -p $(DESTDIR)/usr/bin $(DESTDIR)/usr/share/adminkit \
	$(DESTDIR)$(CFGDIR)/roles $(DESTDIR)$(CFGDIR)/files \
	$(DESTDIR)$(CFGDIR)/once \
	$(DESTDIR)$(CFGDIR)/adminkit.conf.d
	install adminkit $(DESTDIR)/usr/bin/
	install -m 644 adminkit.py $(DESTDIR)/usr/share/adminkit/
	install -m 755 update-adminkit.conf $(DESTDIR)/usr/share/adminkit/

clean:
	rm -f *~ *.pyc
	cd docs; make clean
