all:

install:
	mkdir -p $(DESTDIR)/usr/bin $(DESTDIR)/usr/share/adminkit \
	$(DESTDIR)/var/lib/adminkit/roles $(DESTDIR)/var/lib/adminkit/files
	install adminkit $(DESTDIR)/usr/bin/
	install -m 644 adminkit.py $(DESTDIR)/usr/share/adminkit/
	install -m 644 adminkit.conf $(DESTDIR)/var/lib/adminkit/

clean:
	rm -f *~ *.pyc
