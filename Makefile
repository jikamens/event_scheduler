README.txt: event_scheduler/scheduler.py
	python3 -m pydoc $^ | perl -e '$$/ = undef; $$_ = <>; s/\n\s*\nFILE\n.*/\n/s; print' > $@.tmp
	mv $@.tmp $@
