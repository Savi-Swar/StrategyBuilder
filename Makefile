# Quark — one entry point per pipeline. Every target is safe to re-run:
# refresh is full-replace per ticker (append-free by design, so a re-run of
# any day converges to the same DB), backfill re-fetches a closed date range
# and dedupes into the existing artifact.

FROM ?= 2012-01-01
TO   ?= $(shell date +%Y-%m-%d)

.PHONY: test refresh terminal research backfill desk all

test:
	python3 -m pytest -q

refresh:            ## full-replace refresh of all price data (idempotent)
	python3 scripts/refresh_data.py

terminal:           ## rebuild all Vig screens from the current DB
	python3 scripts/update_dashboard.py --skip-refresh --no-llm --no-news

research:           ## regenerate the research record (screen 06)
	python3 scripts/make_research_site.py

backfill:           ## re-fetch EDGAR 8-K announcement dates for [FROM, TO]
	python3 scripts/fetch_8k_async.py --start $(FROM) --end $(TO)

desk:               ## regenerate the paper-desk screen from live ledgers
	python3 /Users/swarup44891/moneymaker3000/desk_page.py

all: refresh terminal research
