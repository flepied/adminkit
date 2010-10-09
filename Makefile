CFGDIR=/var/lib/adminkit

all:

install:
	mkdir -p $(DESTDIR)/usr/bin $(DESTDIR)/usr/share/adminkit \
	$(DESTDIR)$(CFGDIR)/roles $(DESTDIR)$(CFGDIR)/files \
	$(DESTDIR)$(CFGDIR)/adminkit.conf.d
	install adminkit $(DESTDIR)/usr/bin/
	install -m 644 adminkit.py $(DESTDIR)/usr/share/adminkit/
	install -m 755 update-adminkit.conf $(DESTDIR)/usr/share/adminkit/
	install -m 644 adminkit.conf $(DESTDIR)$(CFGDIR)/adminkit.conf.d/00system.conf

clean:
	rm -f *~ *.pyc
