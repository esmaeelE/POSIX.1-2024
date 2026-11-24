.PHONY: all convert build serve check-links

all: convert build check-links

convert:
	python3 convert_to_mdbook.py

build:
	cd susv5-book && mdbook build

serve:
	cd susv5-book && mdbook serve -o

check-links:
	python3 scripts/check_links.py
