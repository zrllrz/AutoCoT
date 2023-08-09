#!/bin/bash

cd src &&

CUDA_VISIBLE_DEVICES=0 python label.py \
   --task=PegInsertionSide-v0 --control_mode=pd_joint_delta_pos --obs_mode=state \
   --seed=0 \
   --n_traj=10 \
   --model_name=HARD_GPT_k4-c10_KT1.0-gpt_s3_a1-emb128-key128-e128 \
   --from_ckpt=1000 \

