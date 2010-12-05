#!/bin/sh
#---------------------------------------------------------------
# Project         : tests
# File            : tests.sh
# Copyright       : (C) 2010 by Frederic Lepied
# Author          : Frederic Lepied
# Created On      : Sat Dec  4 23:23:23 2010
# Purpose         : tests driver for adminkit
#---------------------------------------------------------------

TOP=`dirname $0`
ORG=`pwd`

run_adminkit()
{
    [ -d roles ] || cd $TOP/$1
    mkdir -p once dest
    fakeroot ../../adminkit -R $PWD/ -D $PWD/dest/ adminkit.conf
    assertEquals "error running adminkit for $1" $? 0
}

clean_result()
{
    rm -rf $PWD/dest/*
    rm -rf $PWD/vars $PWD/once
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

. /usr/share/shunit2/shunit2

# tests.sh ends here
