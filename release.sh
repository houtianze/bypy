#!/bin/sh

set -o errexit

actual=0
build=0
upload=0
testit=0
while getopts "abut" opt; do
	case "$opt" in
	a)
		actual=1
		;;
	b)
		build=1
		;;
	u)
		build=1
		upload=1
		;;
	t)
		testit=1
		;;
	esac
done

if [ "$testit" -eq 1 ]
then
	python2 -m pyflakes bypy.py test/test.py
	python2 setup.py test
	python2 -m doctest -v bypy.py

	python3 -m pyflakes bypy.py test/test.py
	python3 setup.py test
	python3 -m doctest -v bypy.py
fi


if [ "$build" -eq 1 ]
then
	rm -Rf dist/*
	python3 setup.py sdist bdist_wheel
fi

if [ "$actual" -eq 0 ]
then
	repoopt="-r testpypi"
	indexopt="-i https://testpypi.python.org/simple/"
else
	repoopt=""
	indexopt=""
fi

uploadcmd="twine upload dist/* $repoopt"
if [ "$upload" -eq 0 ]
then
	echo "$uploadcmd"
else
	eval "$uploadcmd"
fi

. ~/Documents/t/venv27/bin/activate
pip install -U bypy $indexopt
bypy -V
bypy quota
deactivate
. ~/Documents/t/venv34/bin/activate
pip install -U bypy $indexopt
bypy -V
bypy quota
deactivate

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
