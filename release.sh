#!/bin/sh

set -o errexit
#set -x

py2venv="$HOME/Documents/t/venv27"
py3venv="$HOME/Documents/t/venv34"
if [ ! -d "$py2venv" ]
then
  python2 -m virtualenv "$py2venv"
fi

if [ ! -d "$py3venv" ]
then
  python3 -m virtualenv "$py3venv"
fi

actual=0
build=0
install=0
upload=0
testit=0
while getopts "abuit" opt; do
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
		testit=1
		install=1
		;;
	i)
		install=1
		;;
	t)
		testit=1
		;;
	esac
done

if [ "$actual" -eq 0 ]
then
	repoopt="-r testpypi"
	indexopt="-i https://testpypi.python.org/simple/"
else
	repoopt=""
	indexopt=""
fi

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
	python3 setup.py sdist # bdist_wheel
fi

uploadcmd="twine upload dist/* $repoopt"
if [ "$upload" -eq 0 ]
then
	echo "$uploadcmd"
else
	eval "$uploadcmd"
fi

if [ "$install" -eq 1 ]
then
	. "$py2venv/bin/activate"
	pip install requests
	pip install pypandoc
	pip install -U bypy $indexopt
	bypy -V
	bypy quota
	deactivate
	. "$py3venv/bin/activate"
	pip install requests
	pip install pypandoc
	pip install -U bypy $indexopt
	bypy -V
	bypy quota
	deactivate
fi

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
