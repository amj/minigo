
WORK_DIR=$1
export BOARD_SIZE=9 
for i in {1..5}; do
  D=$WORK_DIR$i
  echo $D
python ml_perf/reference_implementation.py --bootstrap --flagfile=ml_perf/flags/9/rl_loop.flags --base_dir=$D 
rm -rfd $D/data
done
