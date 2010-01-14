all:

install:
	mkdir -p $(DESTDIR)/etc/adminkit $(DESTDIR)/usr/bin $(DESTDIR)/usr/share/adminkit $(DESTDIR)/var/lib/adminkit
	install adminkit $(DESTDIR)/usr/bin/
	install -m 644 adminkit.py $(DESTDIR)/usr/share/adminkit/
	install -m 644 adminkit.conf $(DESTDIR)/etc/adminkit/

clean:
	rm -f *~ *.pyc
