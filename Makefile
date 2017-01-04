
RESOURCES=jouvence/resources

all: $(RESOURCES)/html_styles.css

%.css: %.scss
	scss $< $@
