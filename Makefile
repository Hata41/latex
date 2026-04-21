PROJECTS = oleron linucb maze

all:
	for dir in $(PROJECTS); do \
		$(MAKE) -C $$dir; \
	done

animate:
	$(MAKE) -C oleron animate

clean:
	for dir in $(PROJECTS); do \
		$(MAKE) -C $$dir clean; \
	done

sync:
	uv sync

.PHONY: all clean sync animate
