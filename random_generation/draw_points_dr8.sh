#!/bin/bash
export name_for_run=dr9m_test
export obiwan_out=$CSCRATCH/Obiwan/dr9m/obiwan_out/$name_for_run/
export TOTAL_POINTS=5000000
#mkdir $obiwan_out
mkdir $obiwan_out/randoms_chunk
python draw_points_dr8.py

rm $obiwan_out/randoms_chunk/randoms_*
