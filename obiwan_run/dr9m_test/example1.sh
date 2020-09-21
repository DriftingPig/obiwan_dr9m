#!/bin/bash -l
#source /srv/py3_venv/bin/activate
export PYTHONPATH=$CSCRATCH/Obiwan/dr9m/obiwan_code/py:$PYTHONPATH

python ./example1.py $name_for_run
