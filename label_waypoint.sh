#!/bin/bash

TASK=PegInsertionSide-v0

cd src &&

CUDA_VISIBLE_DEVICES=3 python label_waypoint.py \
  --task=$TASK --control_mode=pd_joint_delta_pos --obs_mode=state \
  --seed=0 \
  --n_traj=-1 \

#for ((i=2000; i<=4000; i+=100));do
#  CUDA_VISIBLE_DEVICES=2 python label.py \
#   --task=StackCube-v0 --control_mode=pd_joint_delta_pos --obs_mode=state \
#   --seed=0 \
#   --n_traj=-1 \
#   --model_name=SC_0908_0755k4-r4-f2-c10_KT0.1_EMA0.9_ema_ave_st-emb1.2-r_l10.0-use_r-egpthn_s2_a1-emb128-key128-e128-cluster0.001-rec0.1-finetune \
#   --from_ckpt=$i \
#   --pause
#done




# 0902
#       PegInsertionSide    StackCube   TurnFaucet-v0
# 2000
# 2100
# 2200
# 2300
# 2400
# 2500
# 2600
# 2700  23.47
# 2800  33.35
# 2900  37.96
# 3000  25.67                           \
# 3100  22.37                           35.342288557213934
# 3200  22.33                           38.208955223880594
# 3300  25.52                           33.15422885572139
# 3400  26.57                           35.6089552238806
# 3500  33.61                           35.744278606965175
# 3600  36.89                           48.12238805970149
# 3700  32.16                           34.73
# 3800  32.73                           28.60
# 3900  27.53               09.30       28.60
# 4000  32.10               16.93       23.81



# 0904
#       PegInsertionSide    StackCube   TurnFaucet-v0
# 3000  24.24               21.46       18.03
# 3100  15.02               24.16       31.76
# 3200  9.34                19.65       30.88
# 3300  9.37                24.04       25.09
# 3400  15.87               15.87       25.33
# 3500  19.21               22.41       23.22
# 3600  50.03               17.33       24.73
# 3700  14.56               10.82       34.54
# 3800  21.78               11.75       49.97
# 3900  8.94                22.03       25.27
# 4000  17.91               24.13       31.18





# 0904
#       PegInsertionSide    StackCube   TurnFaucet-v0    PickCube
# 2000  13.07               13.86       22.75         \
# 2100  8.48                13.06       29.65         \
# 2200  6.80                16.92       31.63         5.87
# 2300  \                   \           27.94         \
# 2400  \                   \           22.92         \
# 2500  \                   \           18.68         \
# 2600  \                   \           25.66         \
# 2700  \                   \           30.61         \
# 2800  \                   \           26.04         \
# 2900  \                   \           22.38         \
# 3000  10.39               11.64       28.07         8.50
# 3100  16.70               22.85       26.03         8.73
# 3200  13.34               16.75       28.84         4.18
# 3300  20.43               13.27       30.90         3.07
# 3400  24.81               11.59       28.38         9.29
# 3500  9.05                14.48       43.84         8.76
# 3600  30.83               16.70       26.65         4.92
# 3700  14.51               11.41       37.49         3.61
# 3800  25.41               9.65        36.97         \
# 3900  39.73               17.99       44.30         3.60
# 4000  20.58               13.99       24.40         5.91


# 0905
#       PegInsertionSide  StackCube   TurnFaucet-v0    PickCube
# 2000  13.07             \           \             \
# 2100  8.48              \           27.04         \
# 2200  6.80              \           31.55         5.87
# 2300  \                 \           26.75         \
# 2400  \                 \           34.89          \
# 2500  \                 \           30.07         \
# 2600  \                 \           32.71         \
# 2700  \                 \           32.40         \
# 2800  \                 \           31.57         \
# 2900  \                 \           32.58         \
# 3000  10.39             10.00       24.88         8.50
# 3100  16.70             8.98        20.68         8.73
# 3200  13.34             9.04        30.42         4.18
# 3300  20.43             13.78       29.05         3.07
# 3400  24.81             18.90       32.06         9.29
# 3500  9.05              15.07       31.67         8.76
# 3600  30.83             24.15       35.02         4.92
# 3700  14.51             14.48       40.56         3.61
# 3800  25.41             21.74       36.24         \
# 3900  39.73             23.14       36.93         3.60
# 4000  20.58             21.36       34.79         5.91


# WODG
#       PegInsertionSide  StackCube
# 2000  47.99             25.62
# 2100  47.40             25.55
# 2200  47.28             28.99
# 2300  40.38             31.28
# 2400  40.22             23.11
# 2500  37.11             29.77
# 2600  43.33             30.90
# 2700  46.11             40.02
# 2800  45.41             36.68
# 2900  45.74             24.37
# 3000  42.49             25.94
# 3100  35.52             24.71
# 3200  38.18             24.84
# 3300  46.23             23.15
# 3400  41.11             24.79
# 3500  41.67             23.18
# 3600  32.06             24.92
# 3700  41.34             24.72
# 3800  43.96             25.72
# 3900  36.37             24.01
# 4000  38.57             26.80

# WOSG
#       PegInsertionSide  StackCube
# 2000  18.97             13.96
# 2100  28.87             20.81
# 2200  11.91             18.14
# 2300  11.05             20.93
# 2400  12.75             17.23
# 2500  33.68             26.16
# 2600  42.10             10.97
# 2700  25.78             9.17
# 2800  20.41             17.50
# 2900  37.98             9.37
# 3000  23.99             11.94
# 3100  14.60             21.55
# 3200  17.05             22.42
# 3300  12.52             16.14
# 3400  13.92            `12.35
# 3500  19.12             9.30
# 3600  18.36             21.78
# 3700  23.46             6.06
# 3800  19.43             9.39
# 3900  16.16             26.22
# 4000  13.01             17.14

