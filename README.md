test
mkdir $CSCRATCH/Obiwan
mkdir $CSCRATCH/Obiwan/obiwan_code
git clone ....

in obiwan_code:
export name_for_run=XXX
this parameter should be set the same in all file it appears for each run

brickstat: it takes records on the bricks unfinished&finished in each run and generate a list of bricks that needs to be processed
usage: store the list of bricks you want to process in e.g. real_brick_lists/bricks_dr9f_south.txt
python brickstat.py --name_for_run dr9m_test --rs rs0 --real_bricks_fn bricks_dr9f_south.txt
you need to change the first line: 
obiwan_out_dir = '/global/cscratch1/sd/huikong/Obiwan/dr9m/obiwan_out/NAME4RUN/output/'
to your corresponds directory

random_generation: generates random from some seed, usually distribute some seed to a uniform area
this is just a reference code because different project generate randoms differently, you should write your own code for randoms you want to get
you should store the randoms you generated in $obiwan_out/$name_for_run/randoms_chunk/stacked_randoms.fits for future process
(I'm going to make this part better readable later...)


random_division: 
change all the necessary parameters in the slurm file, then submit it. you should get a divided_randoms directory which divided your stacked_randoms.fits into each bricks

obiwan_run:
run obiwan
outputs should all be in $obiwan_out/output
srun -n (number of nodes) -c (number of nodes)*4 


TO CONSTRUCT A obiwan_data directory:
make a directory called 'obiwan_data'
copy these files to this directories in case thier directories get changed
you can also do a softlink since we believe there will not be much change after this version
cp /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/ccds-annotated-* ./
cp /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/survey-* ./

and then:
ln -s /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/calib/ ./
ln -s /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/images/ ./


(More analysis code will be posted when I clean them up)
