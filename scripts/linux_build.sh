#!/bin/bash
docker build -t civ-package-linux .
docker run --rm -v "$(pwd)":/app civ-package-linux
