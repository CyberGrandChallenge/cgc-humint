MAN_DIR      = $(DESTDIR)/usr/share/man/man1
BIN_DIR      = $(DESTDIR)/usr/bin
SHARE_DIR	 = $(DESTDIR)/usr/share/cgc-humint
PY_DIR		 = $(DESTDIR)/usr/lib/pymodules/python2.7
BINS		 = cbgen

MAN			 = $(addsuffix .1.gz,$(BINS))

all: man

man: $(MAN)

%.1.gz: %.md
	pandoc -s -t man $< -o $<.tmp
	gzip -9 < $<.tmp > $@

install:
	install -d $(BIN_DIR)
	install bin/$(BINS) $(BIN_DIR)
	install -d $(MAN_DIR)
	install $(MAN) $(MAN_DIR)
	install -d $(SHARE_DIR)
	cp -r templates $(SHARE_DIR)/templates
	cp -r configs $(SHARE_DIR)/configs
	find $(SHARE_DIR) -type d -name .svn -print|xargs rm -rf
	install -d $(PY_DIR)/cbgen
	install cbgen/*.py $(PY_DIR)/cbgen

clean:
	rm -f *.1.gz *.tmp
