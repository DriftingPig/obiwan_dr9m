mkdir -p $CSCRATCH/Obiwan/dr9m

cd $CSCRATCH/Obiwan/dr9m

git clone https://github.com/DriftingPig/obiwan_dr9m.git

mv obiwan_dr9m obiwan_code

mkdir obiwan_data

mkdir obiwan_out

cd obiwan_data

cp /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/ccds-annotated-* ./

cp /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/survey-* ./

ln -s /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/calib/ ./

ln -s /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/images/ ./

cd ../obiwan_out

#choose a name for your run, it's the same as the environment varible name_for_run, this time we choose 'test'

mkdir test

cd test

mkdir randoms_chunk

#the random you generated in the way you want, there is no universal code for that. For testing, copy a fits file from my directory:

cp /global/cscratch1/sd/huikong/Obiwan/stacked_randoms.fits ./randoms_chunk

#make a bricklist for all the bricks you want to process. For testing, you can copy a demo one first

cp /global/cscratch1/sd/huikong//Obiwan/dr9m/obiwan_code/brickstat/real_brick_lists/bricks_dr9f_south.txt  bricklist.txt 

cd ../../obiwan_code/brickstat

mkdir test

#this will generate a directoy called 'test', with file 'FinishedBricks.txt' and 'UnfinishedBricks.txt' 

python brickstat.py --name_for_run test --rs rs0 --real_bricks_fn bricks_dr9f_south.txt

cd ../random_division


#OPEN slurm_submit.sh, change 'export name_for_run=dr9m_test' to 'export name_for_run=test'

#divide the randoms into each bricks for future process

sbatch slurm_submit.sh

#wait until job is finished. It generates per brick randoms in $CSCRATCH/Obiwan/dr9m/obiwan_out/test/divided_randoms, you can take a look

cd ../obiwan_run

mkdir test

cd test

mkdir slurm_output

#OPEN slurm_all_bricks.sh, change 'export name_for_run=dr9m_test' to 'export name_for_run=test', and you need to decide the time and number of nodes need for the run. The nodes  must be bigger than 2

sbatch slurm_all_bricks.sh

If you have any questions and problem during setup, my email address is: kong.291@osu.edu


(More analysis code will be posted when I clean them up)
