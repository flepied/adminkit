#!/bin/sh
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
    run_adminkit test1
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
    run_adminkit test2
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
    run_adminkit test3
    clean_result
}

testInclude()
{
    run_adminkit test4
    cmp $PWD/dest/etc/p /etc/passwd
    assertEquals 'copy is different' $? 0
    cmp $PWD/files/etc/toto $PWD/dest/etc/test
    assertEquals 'copy is different' $? 0
    clean_result
}

testGlobal()
{
    run_adminkit test5
    assertEquals 'error processing global directive' $? 0
    clean_result
}

testFilename()
{
    run_adminkit test6
    assertEquals 'error processing global directive' $? 0
    [ -d $PWD/dest/etc-`hostname -d` ]
    assertEquals 'file not created with the right name' $? 0
    clean_result
}

testList()
{
    run_adminkit test7
    assertEquals 'error processing add_to_list directive' $? 0
    clean_result
}

testVars()
{
    run_adminkit test8
    assertEquals 'error processing add_to_list directive' $? 0
    clean_result
}

testFuture()
{
    OPT=-f
    mkdir -p $TOP/test9/dest/etc/
    rm -f $TOP/test9/dest/etc/test
    touch $TOP/test9/vars
    touch -t 202201010000 $TOP/test9/dest/etc/test
    run_adminkit test9
    cmp $PWD/dest/etc/test $PWD/files/etc/test
    assertEquals 'error forcing copy from the future' $? 0
    clean_result
}

. /usr/share/shunit2/shunit2

# tests.sh ends here
