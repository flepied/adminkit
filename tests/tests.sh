#!/bin/bash
#---------------------------------------------------------------
# Project         : tests
# File            : tests.sh
# Copyright       : (C) 2010,2011 by Frederic Lepied
# Author          : Frederic Lepied
# Created On      : Sat Dec  4 23:23:23 2010
# Purpose         : tests driver for adminkit
#---------------------------------------------------------------

TOP=`dirname $0`
ORG=`pwd`
OPT=

run_adminkit()
{
    [ -d roles ] || cd $TOP/$1
    mkdir -p once dest
    if [ -n "$2" ]; then
	DRIVER="$2"
    else
	DRIVER=adminkit
    fi
    fakeroot ../../$DRIVER $OPT -R $PWD/ -D $PWD/dest/ adminkit.conf
    assertEquals "error running adminkit for $1" $? 0
}

clean_result()
{
    OPT=
    rm -rf $PWD/dest/*
    rm -rf $PWD/vars $PWD/top/vars $PWD/once
    cd $ORG
}

testCopy()
{
    run_adminkit testCopy
    cmp $PWD/files/etc/test $PWD/dest/etc/test
    assertEquals 'copy is different' $? 0
    touch -r $PWD/dest/etc/test $PWD/dest/ref
    run_adminkit test1
    [ $PWD/dest/etc/test -nt $PWD/dest/ref ]
    assertNotEquals 'second run modified file' $? 0
    clean_result
}

testCopyWithSpecs()
{
    run_adminkit testCopyWithSpecs
    [ -x $PWD/dest/etc/test ]
    assertEquals 'file is not executable' $? 0
    touch -r $PWD/dest/etc/test $PWD/dest/ref
    run_adminkit test2
    [ $PWD/dest/etc/test -nt $PWD/dest/ref ]
    assertNotEquals 'second run modified file' $? 0
    clean_result
}

testPkg()
{
    run_adminkit testPkg
    clean_result
}

testInclude()
{
    run_adminkit testInclude
    cmp $PWD/dest/etc/p /etc/hosts
    assertEquals 'copy is different' $? 0
    cmp $PWD/files/etc/toto $PWD/dest/etc/test
    assertEquals 'copy is different' $? 0
    clean_result
}

testGlobal()
{
    run_adminkit testGlobal
    assertEquals 'error processing global directive' $? 0
    clean_result
}

testFilename()
{
    run_adminkit testFilename
    assertEquals 'error processing global directive' $? 0
    [ -f $PWD/dest/etc-`hostname`/test.`hostname` ]
    assertEquals 'file not created with the right name' $? 0
    clean_result
}

testList()
{
    run_adminkit testList
    assertEquals 'error processing add_to_list directive' $? 0
    clean_result
}

testFuture()
{
    OPT=-f
    mkdir -p $TOP/testFuture/dest/etc/
    rm -f $TOP/testFuture/dest/etc/test
    touch $TOP/testFuture/vars
    touch -t 202201010000 $TOP/testFuture/dest/etc/test
    run_adminkit testFuture
    cmp $PWD/dest/etc/test $PWD/files/etc/test
    assertEquals 'error forcing copy from the future' $? 0
    clean_result
}

testNagios()
{
    run_adminkit testNagios
    assertEquals 'error processing global directive for Nagios' $? 0
    clean_result
}

if [ -r /usr/share/shunit2/shunit2 ]; then
    SHUNIT2=/usr/share/shunit2/shunit2
else
    RELDIR=`dirname $0`
    ABSDIR=`cd $RELDIR/..; pwd`
    if [ -r "$ABSDIR/shunit2/shunit2" ]; then
	SHUNIT2="$ABSDIR/shunit2/shunit2"
    elif [ -r "$ABSDIR/shunit2/src/shunit2" ] ;then
	SHUNIT2="$ABSDIR/shunit2/src/shunit2"
    else
	echo "Unable to find shunit2" 1>&2
	exit 1
    fi
fi

if ! type fakeroot >& /dev/null; then
    echo "Unable to find fakeroot" 1>&2
    exit 1
fi

. $SHUNIT2

# tests.sh ends here
