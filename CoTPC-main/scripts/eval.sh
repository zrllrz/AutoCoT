#!/bin/bash

MODEL_DIR="../save_model/"
TASK=StackCube-v0
MODEL_NAME=SC-0919-MIDDLE
I=2184000

cd ../src &&

#CUDA_VISIBLE_DEVICES=6 python eval.py --eval_max_steps=300 \
#    --from_ckpt=1780000 --task=TurnFaucet-v0-v0 \
#    --model_name=TF-0905 \

while [[ $I -ge 1000000 ]];
do
  echo "$MODEL_DIR$MODEL_NAME""/""$I.pth"
  if test -e "$MODEL_DIR$MODEL_NAME""/""$I.pth"; then
    CUDA_VISIBLE_DEVICES=0 python eval.py \
      --eval_max_steps=200 \
      --from_ckpt=$I \
      --task=$TASK \
      --model_name=$MODEL_NAME \
      --n_env=25
  else
    echo "wait"
  fi
  ((I-=2000))
done

#for ((i=1000000; i<=1800000; i+=20000));do
#  CUDA_VISIBLE_DEVICES=0 python eval.py --eval_max_steps=250 --from_ckpt=$i --task=StackCube-v0 --model_name=SC-0903
#done




#           PegInsertionSide              StackCube                     TurnFaucet-v0                        PickCube
# ITER      TRAIN SUCC  TEST SUCC         TRAIN SUCC  TEST SUCC         TRAIN SUCC  TEST SUCC             TRAIN SUCC  TEST SUCC
# 0903      61.00%      31.00% (1.74e6)   61.00%      31.00% (1.74e6)
#                                         60.00%      39.00% (1.54e6)
#                                         58.20%      40.00% (1.52e6)
#
#                                                                       39.00       41.00 20.75 (1.00e6)
#                                                                       40.80       33.00 13.00 (1.02e6)
#                                                                       43.00       33.00 19.00 (1.04e6)
#                                                                       39.80       43.00 17.00 (1.06e6)
#                                                                       38.00       37.00 15.00 (1.08e6)
#                                                                       40.20       34.00 16.50 (1.10e6)
#                                                                       39.80       42.00 19.00 (1.12e6)
#                                                                       41.80       44.00 12.25 (1.14e6)
#                                                                       39.00       39.00 17.00 (1.16e6)
#                                                                       40.00       34.00 15.00 (1.18e6)
#                                                                       43.00       44.00 16.25 (1.20e6)
#                                                                       41.20       37.00 16.50 (1.22e6)
#                                                                       37.60       36.00 15.00 (1.24e6)
#                                                                       41.00       44.00 14.00 (1.26e6)
#                                                                       40.80       39.00 15.50 (1.28e6)
#                                                                       44.40       42.00 16.50 (1.30e6)
#                                                                       39.80       40.00 21.25 (1.32e6)
#                                                                       41.40       37.00 14.00 (1.34e6)
#                                                                       39.60       40.00 15.00 (1.36e6)
#                                                                       41.00       38.00 20.50 (1.38e6)
#                                                                       41.40       39.00 17.75 (1.40e6)
#                                                                       40.20       41.00 15.25 (1.42e6)
#                                                                       41.80       41.00 15.25 (1.44e6)
#                                                                       39.20       40.00 16.50 (1.46e6)
#                                                                       37.40       39.00 17.75 (1.48e6)
#                                                                       39.00       35.00 16.75 (1.50e6)
#                                                                       38.40       37.00 16.25 (1.52e6)
#                                                                       40.80       44.00 19.75 (1.54e6)
#                                                                       39.20       40.00 17.00 (1.56e6)
#                                                                       39.20       40.00 15.25 (1.58e6)
#                                                                       41.40       41.00 17.75 (1.60e6)
#                                                                       39.60       40.00 15.75 (1.62e6)
#                                                                       39.00       36.00 19.50 (1.64e6)
#                                                                       36.40       36.00 15.00 (1.66e6)
#                                                                       39.60       40.00 16.25 (1.68e6)
#                                                                       37.40       36.00 17.25 (1.70e6)
#                                                                       39.00       39.00 17.50 (1.72e6)
#                                                                       37.80       38.00 16.25 (1.74e6)
#                                                                       37.60       38.00 17.50 (1.76e6)
#                                                                       37.00       37.00 18.00 (1.78e6)
#                                                                       40.60       43.00 19.00 (1.80e6)
#
# 0904                                                                  32.80       32.00 18.75 (1.70e6)
#                                                                       33.20       28.00 16.25 (1.68e6)
#                                                                       34.80       31.00 15.00 (1.66e6)
#                                                                       33.80       29.00 16.25 (1.64e6)
#                                                                       34.40       35.00 15.00 (1.62e6)
#                                                                       34.60       36.00 16.50 (1.60e6)
#                                                                       33.20       33.00 14.50 (1.58e6)
#                                                                       33.00       33.00 13.50 (1.56e6)
#                                                                       33.00       35.00 16.25 (1.54e6)
#                                                                       34.60       30.00 16.25 (1.52e6)
#                                                                       33.80       32.00 17.25 (1.50e6)
#                                                                       33.80       36.00 16.00 (1.48e6)
#                                                                       31.60       32.00 18.50 (1.46e6)
#                                                                       31.80       33.80 15.50 (1.44e6)
#                                                                       33.60       38.00 15.50 (1.42e6)
#                                                                       30.60       32.00 14.25 (1.40e6)
#                                                                       32.20       35.00 18.25 (1.38e6)
#                                                                       34.80       35.00 11.75 (1.36e6)
#                                                                       32.40       33.00 13.75 (1.34e6)
#                                                                       33.80       36.00 12.25 (1.32e6)
#                                                                       36.40       38.00 17.25 (1.30e6)
#                                                                       34.00       34.00 18.00 (1.28e6)
#                                                                       32.20       34.00 10.00 (1.26e6)
#                                                                       30.00       40.00 15.25 (1.24e6)
#                                                                       34.80       33.00 12.25 (1.22e6)
#                                                                       34.80       33.00 12.25 (1.22e6)
#                                                                       33.60       35.00 15.00 (1.20e6)
#                                                                       33.60       35.00 15.00 (1.18e6)
#                                                                       26.60       27.00 20.00 (1.16e6)
#                                                                       29.00       35.00 11.00 (1.14e6)
#
# 0905
#
#
#




# 40_000    0.20%       0.00%         \           \             \           \             \           \
# 80_000    4.00%       1.00%         \           \             \           \             \           \
# 120_000   8.60%       3.00%         \           \             \           \             \           \
# 160_000   1.20%       0.75%         \           \             \           \             \           \
# 200_000   3.40%       3.25%         \           \             \           \             \           \
# 240_000   23.20%      4.75%         \           \             \           \             \           \
# 280_000   3.40%       0.75%         \           \             \           \             \           \
# 320_000   4.80%       2.0%          \           \             \           \             \           \
# 360_000   10.40%      3.25%         \           \             \           \             \           \
# 400_000   9.40%       1.75%         \           \             \           \             \           \
# 440_000   0.80%       1.75%         \           \             \           \             \           \
# 480_000   6.20%       2.00%         \           \             \           \             \           \
# 520_000   11.00%      1.50%         \           \             \           \             \           \
# 560_000   33.40%      6.25%         \           \             \           \             \           \
# 600_000   15.80%      4.25%         \           \             \           \             \           \
# 640_000   24.00%      4.75%         \           \             \           \             \           \
# 680_000   35.80%      5.50%         \           \             \           \             \           \
# 720_000   25.60%      2.75%         \           \             \           \             \           \
# 760_000   14.40%      5.25%         \           \             \           \             \           \
# 800_000   19.40%      7.50%         \           \             \           \             \           \
# 840_000   15.00%      5.25%         \           \             \           \             \           \
# 880_000   15.00%      8.25%         \           \             \           \             \           \
# 920_000   41.00%      10.75%        \           \             \           \             \           \
# 960_000   45.60%      15.25%        \           \             \           \             \           \
# 1_000_000 31.00%      11.25%        26.40%      15.00%
# 1_040_000 35.60%      13.75%        30.20%      16.00%
# 1_080_000 25.80%      8.00%         37.80%      16.00%
# 1_120_000 29.60%      11.25%        33.60%      13.00%
# 1_160_000 32.60%      9.75%         31.60%      13.00%
# 1_200_000 59.80%      14.25%        33.00%      16.00%                                  75.60%      74.00%
# 1_240_000 57.60%      14.00%        33.00%      14.00%
# 1_280_000 44.20%      13.75%        36.40%      19.00%
# 1_320_000 56.60%      14.50%        34.40%      20.00%
# 1_360_000 59.40%      15.50%        35.00%      17.00%
# 1_400_000 54.60%      13.50%        33.40%      17.00%                                  78.40%      72.00%
# 1_440_000 46.20%      12.00%        33.40%      24.00%
# 1_480_000 65.60%      14.00%
# 1_520_000 66.40%      16.00%        57.00%      22.00%
# 1_560_000 62.60%      15.50%        56.60%      16.00%
# 1_600_000 54.60%      13.50%        36.80%      19.00%
# 1_640_000 59.60%      14.50%
# 1_680_000 55.40%      13.75%
# 1_720_000 63.60%      17.75%
# 1_760_000 57.80%      14.00%
# 1_800_000 54.20%      15.25%
