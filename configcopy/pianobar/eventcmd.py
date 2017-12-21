#!/usr/bin/env python
import sys, json, requests

if __name__ == '__main__':
    action = sys.argv[1]
    args = {}
    for line in sys.stdin:
        l = line.split("=")
        args[l[0]] = l[1]
    requests.post('http://localhost/pianobar/' + action, json=args)
