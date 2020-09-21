#! /bin/bash

# Script for running the legacypipe code within a Shifter container at NERSC
# with burst buffer!
# This merges some contents from legacypipe-env and runbrick.sh
# Arguments:
# {0}: LEGACY_SURVEY_DIR
# {1}: brickname
# {2}: stage and write-stage
# {3}: run argument / telescope
# {4}: maxmem, in KB (93750000 total for knl, 125000000 total for haswell)
# {5}: threads
#writecat decam 125000000 $threads
export LEGACY_SURVEY_DIR=$CSCRATCH/Obiwan/dr9m/obiwan_data
BB=${LEGACY_SURVEY_DIR}/
echo $BB
export DUST_DIR=/global/cfs/projectdirs/cosmo/data/dust/v0_1
export UNWISE_COADDS_DIR=/global/cfs/projectdirs/cosmo/work/wise/outputs/merge/neo5/fulldepth:/global/cfs/projectdirs/cosmo/data/unwise/allwise/unwise-coadds/fulldepth
export UNWISE_COADDS_TIMERESOLVED_DIR=/global/cfs/projectdirs/cosmo/work/wise/outputs/merge/neo5
export UNWISE_MODEL_SKY_DIR=/global/cfs/cdirs/cosmo/work/wise/unwise_catalog/dr2/mod
export GAIA_CAT_DIR=/global/cfs/projectdirs/cosmo/work/gaia/chunks-gaia-dr2-astrom-2
export GAIA_CAT_VER=2
export TYCHO2_KD_DIR=/global/cfs/projectdirs/cosmo/staging/tycho2
export LARGEGALAXIES_CAT=/global/cfs/projectdirs/cosmo/staging/largegalaxies/v6.0/LSLGA-model-v6.0.kd.fits
export PS1CAT_DIR=/global/cfs/projectdirs/cosmo/work/ps1/cats/chunks-qz-star-v3
export SKY_TEMPLATE_DIR=/global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/calib/sky_pattern


export PYTHONPATH=$CSCRATCH/Obiwan/dr9m/obiwan_code/legacypipe/py:/usr/local/lib/python:/usr/local/lib/python3.6/dist-packages:/src/unwise_psf/py:.

# Don't add ~/.local/ to Python's sys.path
export PYTHONNOUSERSITE=1

# Force MKL single-threaded
# https://software.intel.com/en-us/articles/using-threaded-intel-mkl-in-multi-thread-application
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1

# To avoid problems with MPI and Python multiprocessing
export MPICH_GNI_FORK_MODE=FULLCOPY
export KMP_AFFINITY=disabled

# Try limiting memory to avoid killing the whole MPI job...
# 16 is the default for both Edison and Cori: it corresponds
# to 3 and 4 bricks per node respectively.
ncores=$threads
ulimit -Sv 125000000

# Reduce the number of cores so that a task doesn't use too much memory.
# Using more threads than the number of physical cores usually causes the
# job to run out of memory.
#ncores=8

cd /src/legacypipe/py

outdir=${obiwan_out}

if [ ${do_skipids} == "no" ]; then
if [ ${do_more} == "no" ]; then
export rsdir=rs${rowstart}
else
export rsdir=more_rs${rowstart}
fi
else
if [ ${do_more} == "no" ]; then
export rsdir=skip_rs${rowstart}
else
export rsdir=more_skip_rs${rowstart}
fi
fi

brick="$1"

bri=$(echo $brick | head -c 3)

RANDOMS_FROM_FITS=$CSCRATCH/Obiwan/dr9m/obiwan_out/$name_for_run/divided_randoms/brick_${brick}.fits

log="${outdir}/logs/${bri}/${brick}/${rsdir}/log.$brick"
mkdir -p $(dirname $log)
echo $dirname
echo logging to...${log}

mkdir -p $outdir/metrics/$bri/${brick}/${rsdir}/

echo Logging to: $log
echo Running on $(hostname)

echo -e "\n\n\n" >> $log
echo "-----------------------------------------------------------------------------------------" >> $log
echo "PWD: $(pwd)" >> $log
echo >> $log
ulimit -a >> $log
echo >> $log
#tmplog="/tmp/$brick.log"

echo -e "\nStarting on $(hostname)\n" >> $log
echo "-----------------------------------------------------------------------------------------" >> $log

echo $PYTHONPATH

python $CSCRATCH/Obiwan/dr9m/obiwan_code/py/kenobi.py \
--dataset ${dataset} \
--brick $brick \
--nobj ${nobj} --rowstart ${rowstart} -o ${object} \
--randoms_db ${randoms_db} --outdir $outdir \
--threads $threads \
--do_skipids $do_skipids \
--do_more $do_more --minid $minid \
--randoms_from_fits $RANDOMS_FROM_FITS \
--verbose \
--pickle "${outdir}/pickles/${bri}/${brick}/${rsdir}/runbrick-%(brick)s-%%(stage)s.pickle" \
--ps "${outdir}/metrics/${bri}/${brick}/${rsdir}/ps-${brick}-${SLURM_JOB_ID}.fits" \
--ps-t0 $(date "+%s") \
--write-stage writecat \
--stage writecat \
--no-galaxy-forcepsf \
--less-masking \
--run decam \
>> $log 2>&1




status=$?
#cat $tmplog >> $log
#python legacypipe/rmckpt.py --brick $brick --outdir $outdir
