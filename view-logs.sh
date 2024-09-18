#!/usr/bin/env bash

LESS=-SR hl $(ls -tr logs/*.{jsonl,jsonl.gz}) --config hl_config.yaml
