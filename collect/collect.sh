#!/bin/bash -l

#SBATCH -p debug
#SBATCH -N 3
#SBATCH -t 00:30:00
#SBATCH --account=desi
#SBATCH -J collect
#SBATCH -L SCRATCH,project
#SBATCH -C haswell
#SBATCH --mail-user=kong.291@osu.edu  
#SBATCH --mail-type=ALL
#SBATCH -o ./slurm_output/slurm_%j.out

# NERSC / Cray / Cori / Cori KNL things
export KMP_AFFINITY=disabled
export MPICH_GNI_FORK_MODE=FULLCOPY
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
# Protect against astropy configs
export XDG_CONFIG_HOME=/dev/shm


export name_for_run=dr9m_test
export PYTHONPATH=/global/cscratch1/sd/huikong/Obiwan/dr9m/obiwan_code/py:$PYTHONPATH
export obiwan_out=$CSCRATCH/Obiwan/dr9m/obiwan_out/$name_for_run
mkdir $obiwan_out/subset

desiconda_version=20190311-1.2.7-img
module use /global/common/software/desi/$NERSC_HOST/desiconda/$desiconda_version/modulefiles
module load desiconda

#Change parameters here: tot_counter must match with the requested node '-N'
tot_counter=3 #this is consistent with # of Nodes(-N) requested


counter=0
name_for_random=$name_for_run


while [ $counter -lt $tot_counter ]
do
    echo HI
    srun -N 1 -n 8 -c 8 python collect_mpi.py --name_for_run ${name_for_run} --split_idx $counter --N_split $tot_counter --n_obj 200 --start_id 0 --rs_type rs0 --name_for_randoms $name_for_random &
    let counter=counter+1 
done
 
wait

#stack all the data, this step could be obmitted if the output is too large
echo start stacking finished images, this might be a long time...
srun -N 1 -n 1 -c 64 python stack.py $tot_counter $name_for_run 
#rm the separated files
rm $obiwan_out/subset/sim_${name_for_run}_part*

echo ALL Done
