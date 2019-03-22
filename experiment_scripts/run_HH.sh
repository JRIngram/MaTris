#!/bin/bash
cd ../
mkdir results
for (( i=1; i<=5; i++ ))
do
	python3 ./matris.py -hh 3
done


