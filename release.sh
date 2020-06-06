#!/bin/sh

# !!! RUN THIS SCRIPT UNDER VIRTUALENV !!!
# need to run the following commands before running this release script
# (This is for macOS, and for python virtualenv is recommended)
# --------
# brew install pandoc
# pip3 install pandoc pypandoc twine pyflakes

### Usage ###
# - Testing: ./release.sh -buti
# - Actual: ./release.sh -abigtu

#set -o errexit
#set -x

trap "echo '=== Release script interrupted ==='; exit -1" SIGINT

check() {
	command -v "$1" || { echo "'$1' doesn't exist, aborting."; exit -1; }
}

check git
check python
check pandoc
check pyflakes
check twine
check jq

pycmd=python

actual=0
build=0
install=0
upload=0
testit=0
tagit=0

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

runtest() {
	eval $pycmd -m pyflakes bypy
	eval $pycmd setup.py test
	#eval $pycmd -m doctest -v bypy.py
	eval $pycmd -m bypy -V
	eval $pycmd -m bypy --config-dir bypy/test/configdir quota
}

installtest() {
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
	bypy --config-dir bypy/test/configdir quota
}

main() {
	./syncver.sh
	eval $pycmd genrst.py
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
		runtest
	fi

	if [ "$build" -eq 1 ]
	then
		rm -Rf dist/*
		eval $pycmd setup.py bdist_wheel #sdist
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
		installtest
	fi
}

main $*

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
