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

run_adminkit()
{
    cd $TOP/$1
    ../../adminkit -R $PWD/ -D $PWD/dest/ adminkit.conf
    assertEquals $? 0
}

clean_result()
{
    rm -rf $PWD/dest/*
}

testCopy()
{
    run_adminkit test1
    cmp $PWD/files/etc/test $PWD/dest/etc/test
    assertEquals $? 0
    clean_result
}

. /usr/share/shunit2/shunit2

# tests.sh ends here
