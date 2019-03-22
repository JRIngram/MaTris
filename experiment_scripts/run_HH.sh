#!/bin/bash
cd ../
mkdir results
for (( i=1; i<=25; i++ ))
do
	python3 ./matris.py -hh 10000
done


