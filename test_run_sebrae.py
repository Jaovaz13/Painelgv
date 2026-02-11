#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')

from etl.manual_sources import run_sebrae
if __name__ == "__main__":
    run_sebrae()
