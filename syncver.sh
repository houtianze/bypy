#!/usr/bin/env bash

ver=$(grep __version__ bypy/const.py | sed -e "s/__version__ *= *'//g" -e "s/'//g")
sed -i -e "s/\(^.*\)\"recommendedVersion\".*$/\1\"recommendedVersion\": \"$ver\",/g" update/update.json
# mac sed fix
sedresidue='update/update.json-e'
if [ -f $sedresidue ]; then
	rm -f $sedresidue
fi
