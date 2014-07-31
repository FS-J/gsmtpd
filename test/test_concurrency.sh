#!/bin/bash

for i in {500..10000..500}
do
    echo $i
    python concurrency.py 5001 $i >> async.log
done
