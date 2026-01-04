#!/bin/bash

git add .
git commit -m "Backup push"

printf '\n'
echo "Use your Github PAT"

git push -u origin main
