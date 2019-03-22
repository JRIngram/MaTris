#!/bin/bash
cd ../
mkdir results
for (( i=1; i<=5; i++ ))
do
	python3 ./matris.py -hi 3
done


