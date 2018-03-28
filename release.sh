#!/bin/sh

#set -o errexit
#set -x

py2venv="$HOME/Documents/t/venv27"
py3venv="$HOME/Documents/t/venv34"

actual=0
build=0
install=0
upload=0
testit=0
tagit=0

createvenv() {
	if [ ! -d "$py2venv" ]
	then
		python2 -m virtualenv "$py2venv"
	fi

	if [ ! -d "$py3venv" ]
	then
		python3 -m virtualenv "$py3venv"
	fi
}

parsearg() {
	while getopts "abigtu" opt; do
		case "$opt" in
		a)
			actual=1
			;;
		b)
			build=1
			;;
		u)
			upload=1
			;;
		i)
			install=1
			;;
		t)
			testit=1
			;;
		g)
			tagit=1
			;;
		esac
	done
}

doctest() {
	eval $1 -m pyflakes bypy
	eval $1 setup.py test
	#eval $1 -m doctest -v bypy.py
}

installtest() {
	. "$1"
	# due to requests not in testpypi
	if [ $actual -eq 0 ]
	then
		pip install requests
	else
		pip uninstall -y requests
	fi
	pip uninstall -y bypy
	pip install -U bypy $indexopt
	bypy -V
	bypy quota
	deactivate
}

main() {
	#if [ ! -f 'HISTORY.rst' ]; then
	#	python genrst.py
	#fi
	python genrst.py
	createvenv
	parsearg $*

	if [ "$actual" -eq 0 ]
	then
		repoopt="-r testpypi"
		indexopt="-i https://testpypi.python.org/simple/"
	else
		repoopt=""
		indexopt=""
	fi

	if [ "$tagit" -eq 1 ]
	then
		bypyversion=`grep __version__ bypy/const.py | sed -e "s/__version__ *= *'//g" -e "s/'//g"`
		git tag
		git tag "$bypyversion"
		git push
		git push --tags
		git tag
	fi

	if [ "$testit" -eq 1 ]
	then
		doctest python2
		doctest python3
	fi

	if [ "$build" -eq 1 ]
	then
		rm -Rf dist/*
		python setup.py bdist_wheel #sdist
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
		installtest "$py2venv/bin/activate"
		installtest "$py3venv/bin/activate"
	fi
}

main $*

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
