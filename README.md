# InfoCon
This is the official repository for: **[InfoCon: Concept Discovery with Generative and Discriminative Informativeness](https://openreview.net/forum?id=g6eCbercEc&referrer=%5BAuthor%20Console%5D(%2Fgroup%3Fid%3DICLR.cc%2F2024%2FConference%2FAuthors%23your-submissions))**

<p align="center">
  <img src='github_teaser/infocon.png' width="700"><br>
</p>
<p align="center">
  <img src='github_teaser/gg_and_dg.jpg' width="700"><br>
</p>

## Environment
### Hardware & OS

64 CPUs, NVIDIA GeForce RTX 3090 (NVIDIA-SMI 530.30.02, Driver Version: 530.30.02, CUDA Version: 12.1), Ubuntu 20.04.6 LTS (GNU/Linux 5.15.0-83-generic x86_64)
### Installation

```
conda create -n infocon python=3.9
source activate infocon
pip install -r requirements.txt
```

## Usage

### Preparing Data-set
[[Reference]](https://github.com/SeanJia/CoTPC) [[Download demo trajectories]](https://drive.google.com/drive/folders/1VdunXUlzqAvy-D8MniQ4anhV5LLBfNbJ)

Each folder has a `*.h5` file (for actual trajectories) and a `*.json` file (for metadata regarding the trajectories).
Each task has over 1000 demo trajectories.
Each trajectory comes with a different env configurations (i.e., env seed, which influences object poses, object geometries, etc.).
These demos are generated by replaying the official ManiSkill2 [demos](https://github.com/haosulab/ManiSkill2#demonstrations) or the ones adapted from [this](https://github.com/caiqi/Silver-Bullet-3D/tree/master/No_Restriction) repo with several patches to the ManiSkill2 code (see `/CoTPC-main/maniskill2_patches`).
Provided by CoTPC team, there are additional flags for the tasks indicating the (subjective) ground-truth key states.
For the task `TurnFaucet-v0`, they use a subset of 10 faucet models for the demos.
If you want to generate visual-based demos, please refer to the official ManiSkill2 guidance [here](https://github.com/haosulab/ManiSkill2#demonstrations).

Put the folder of each task under directory `/CoTPC-main/data/`

### Training InfoCon
Use `train.sh` in directory `/`. Parameters:
<details>

`n_iters` Number of training iterations.

`batch_size` Batch size.

`init_lr` The initial learning rate.

`weight_decay` Weight decay coefficient used in optimizer. We always use AdamW.

`beta1` Beta1 in the AdamW optimizer.

`beta2` Beta2 in the AdamW optimizer.

`dropout` Dropout probability.

`lr_schedule` Learning rate schedule. Selection: `CosineAnnealingLRWarmup`, `MultiStepLR`

`t_warmup` (Make sure you're using `CosineAnnealingLRWarmup`) Number of warming-up iterations

`milestones` (Make sure you're using `MultiStepLR`) Number of iterations before decay lr

`gamma` (Make sure you're using `MultiStepLR`) Decay of learning rate after each milestone step

`n_head` Number of attention heads.

`n_embd` Hidden feature dimension.

`dim_key` dimension of 'key' feature vectors. Two usage: Select the compressed parameter for discriminative goal; Reconstruction regularization.

`dim_e` dimension of compressed parameter vector for discriminative goal.

`n_key_layer` Number of attention layers in KeyNet (ANN used for encoding input into feature vectors for two usage: Select the compressed parameter for discriminative goal; Reconstruction regularization).

`n_rec_layer` Number of attention layers in RecNet (ANN used for reconstruction regularization).

`n_future_layer` Number of attention layers in FutureNet (ANN used for extra prediction of action to next state).

`vq_n_e` Max number of concepts by InfoCon.

`vq_use_r` Use learnable radius of concept prototypes learnt by InfoCon.

`vq_coe_ema` ema moving rate used for learning InfoCon code-book.

`vq_ema_ave` Whether to use average vector to update code-book or not. Suggest using it, otherwise it will be unbearable slow (and it seems to be a process which cannot be computed paralleled)

`KT` Temperature for classifier used in code-book of InfoCon

`vq_use_st_emb` Use spherical time step embedding

`vq_st_emb_rate` Division rate for time sphere embedding

`vq_coe_r_l1` Coefficient L1 regularization on length of every prototype

`vq_use_prob_sel_train` If true, using prob sample when training

`vq_use_timestep_appeal` If true, prototype will move close to time in time interval

`coe_cluster` Weighing coefficient Cluster weight

`coe_rec` Weighing coefficient for RecNet (ANN used for reconstruction regularization).

`use_decay_mask_rate` If true, we will mask up some of the update related to clustering, since at early stage of training, the clustering may not be right. The masking rate will decrease along with proceeding of training.

`sa_type` (default 'egpthn' and we only implement this kind) type of SANet (ANN used for discriminative goal)

`n_state_layer` Number of layers for state prediction in SANet (ANN used for discriminative goal)

`n_action_layer` Number of layers (after state prediction) for action prediction in SANet (ANN used for discriminative goal)

`use_skip` If true, use skip connection for HN generated net when using HN

`use_future_state` action='store_true' if True, we will append the future key states when training discriminative goal.

`model_name` Model name prefix.
    
`from_model_name` default='' type=str Name of the pretrained module.

`from_ckpt` Ckpt number of pretrained module.

`task` Task in ManiSkill2.

`control_mode` Control mode used in envs from ManiSkill2.

`obs_mode` State mode used in envs from ManiSkill2.

`seed` Random seed for data spliting.

`num_traj` Number of training trajectories.

`context_length` The maximium length of sequences sampled from demo trajectories in training.

`min_seq_length` The mininum length of sequences sampled from demo trajectories in training.

`save_every` Save module every [input] epoch.

`log_every` Log metrics every [input] iters.

`num_workers` A positive number for fast async data loading.

`multiplier` Duplicate the dataset to reduce data loader overhead.

`train_half` Train half (do not optimize gen goal loss)

`train_mode` Training mode, Selection: `scratch`(Training from a scratch model with random initial parameters), `pretrain`(Training a model with trivial self-supervised learning method), `finetune`(Training a model based on a pretrained model).

</details>

### Labeling by InfoCon
Use `label.sh` in directory `/`. Parameters:
<details>

`task` Task in ManiSkill2.

`control_mode` Control mode used in envs from ManiSkill2.

`obs_mode` State mode used in envs from ManiSkill2.

`seed` Random seed for data spliting.

`n_traj` Number of validation trajectory.

`model_name` Model name to be loaded.

`from_ckpt` Ckpt number of the module to be loaded.

`key_name` File name of labeled out key states.
</details>

### CoTPC Evaluation

Use `train.sh` in directory `/CoTPC-main/scripts/` to train CoTPC policies. Parameters:
<details>

`n_iters` Number of training iterations

`batch_size` dBatch size

`init_lr` The initial learning rate

`weight_decay` Weight decay coefficient used in (AdamW) optimizer

`beta1` Beta1 in the AdamW optimizer

`beta2` Beta2 in the AdamW optimizer

`dropout` Dropout probability

`lr_schedule` Learning rate schedule. Selection: `CosineAnnealingLRWarmup`, `MultiStepLR`

`key_state_coeff` Coefficient for the key state prediction loss.

`model_type` Model type for the CoTPC model. Selection `s`, `s+a`, `s+cot`, `s+a+cot`

`vq_n_e` Length of code book (number of entries) back in InfoCon. Transform it into key_states and key_state_loss, which will cover the effect of other two args

`key_states` Which key states to use (see GPTConfig for the spec. format).

`key_state_loss` Features out of what attention layers to use for key state prediction losses.

`cot_decoder` Specs of the CoT decoder.

`model_name` Model name (for storing ckpts).

`from_model_name` Name of the pretrained model.

`from_ckpt` Ckpt of pretrained model.

`task` Task in ManiSkill2.

`control_mode` Control mode used in envs from ManiSkill2.

`obs_mode` State mode used in envs from ManiSkill2.

`seed` Random seed for data spliting

`num_traj` Number of training trajectories.

`context_length` Context size of CoTPC (the maximium length of sequences sampled from demo trajectories in training).

`min_seq_length` Mininum length of sequences sampled from demo trajectories in training.

`save_every` Save model every [input] iters.

`log_every` log metrics every [input] iters.

`n_layer` Number of attention layers.

`n_head` Number of attention heads.

`n_embd` Hidden feature dimension.

`num_workers` A positive number for fast async data loading.

`multiplier` Duplicate the dataset to reduce data loader overhead.

`keys_name` Duplicate the dataset to reduce data loader overhead.

</details>

Use `eval.sh`in directory `/CoTPC-main/scripts/` to train CoTPC policies. Parameters:
<details>

`task` Task in ManiSkill2.

`control_mode` Control mode used in envs from ManiSkill2.

`obs_mode` State mode used in envs from ManiSkill2.

`seed` Random seed for data spliting.

`model_name` dModel name to be loaded.

`from_ckpt` Ckpt of the model to be loaded.

`eval_max_steps` Max steps allowed in eval.

`cot_decoder` Specs of the CoT decoder.

`n_env` Number of processes for eval.

</details>


<!--
## CoTPC-main/
relates to CoTPC downstream policies.
* **data**: ManiSkill2 data-set.
* **maniskill2_patches**: Some patching code in ManiSkill2 for CoTPC logs. Refer to CoTPC GitHub Repo for details...
* **scripts**: bash scripts for CoTPC training and evaluation.
* **src**: src code related to CoTPC policies.
* **save_model**: checkpoints of CoTPC policies.
## src/
includes the codes of InfoCon, where
* **modules** includes the used DNN modules
  * **GPT.py**: Transformers used in InfoCon
  * **VQ.py**: VQ-VAE used in InfoCon. It is a little bit different from vanilla VQ-VAE. We've tried many kinds of design. Currently we are using **VQClassifierNNTime**.
  * **module_util.py**: Other modules, like some MLPs, time step embedding modules.
  * (currently other source file are unused)
* **autocot.py**: construct different modules into whole InfoCon. Refer to it for the main pipeline of InfoCon.
* **data.py**: load data.
* **vec_env.py**: Relate to ManiSkill2. Vectorize Environments.
* **train.py**: python scripts for InfoCon training.
* **path.py**: log of data and checkpoint file paths.
* **callbacks.py**: Customized Callbacks for PyTorch Lightning training of InfoCon.
* **label.py**: python scripts for labeling key states. Labeled out key states will be stored as .txt file in **CoTPC-main/data/$TASK_DIR$**.
* **his.py**: calculate Human Intuition Score (HIS) when given labeled out key states.
* **util.py**: other modules and functions.
-->


