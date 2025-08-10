.PHONY: xp-demo effects-demo

xp-demo:
	$(MAKE) -C character_creation_package xp-demo

effects-demo:
	$(MAKE) -C character_creation_package effects-demo

save-demo:
	$(MAKE) -C character_creation_package save-demo
