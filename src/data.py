import os
import numpy as np
import h5py

from torch.utils.data.dataset import Dataset
from torch.nn.utils.rnn import pad_sequence
import torch

# Please specify the DATA_PATH (the base folder for storing data) in `path.py`.
from path import DATA_PATH


def stepfunctionlist(milestones):
    """
    return a step function like list with minestones.
    Example:
    minestones = np.ndArray([4, 9, 14])
    we generate a np.ndArray of len 15:
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2]
                 4              9             14
    """
    lens = milestones[-1] + 1
    res = np.zeros(shape=(lens,))
    for ms in milestones:
        res[ms+1:] += 1
    return res


class MS2Demos(Dataset):
    def __init__(
        self,
        data_split='train',
        task='PickCube-v0',
        obs_mode='state',
        control_mode='pd_joint_delta_pos',
        length=-1,  # pick former <length> data from the task!!!
        min_seq_length=None,
        max_seq_length=None,
        with_key_states=False,
        multiplier=20,  # Used for faster data loading.
        seed=None
    ):  # seed for train/test spliting.
        super().__init__()
        self.task = task
        self.data_split = data_split
        self.seed = seed
        self.min_seq_length = min_seq_length  # For sampling trajectories.
        self.max_seq_length = max_seq_length  # For sampling trajectories.
        self.with_key_states = with_key_states  # Whether output key states.
        self.multiplier = multiplier

        # Usually set min and max traj length to be the same value.
        self.max_steps = -1  # Maximum timesteps across all trajectories.
        traj_path = os.path.join(DATA_PATH, 
            f'{task}/trajectory.{obs_mode}.{control_mode}.h5')
        print('Traj path:', traj_path)
        self.data = self.load_demo_dataset(traj_path, length)

        # Cache key states for faster data loading.
        if self.with_key_states:
            self.idx_to_key_states = dict()
            self.idx_to_key_states_label = dict()

    def __len__(self):
        return len(self.data['env_states'])

    def __getitem__(self, index):
        # Offset by one since the last obs does not have a corresponding action.
        # print(self.data.keys())
        # for k, v in self.data.items():
        #     print(k, type(v))
        l = len(self.data['obs'][index]) - 1

        # Sample starting and ending index given the min and max traj length.
        if self.min_seq_length is None and self.max_seq_length is None:
            s_idx, e_idx = 0, l
        else:
            min_length = 0 if self.min_seq_length is None else self.min_seq_length
            max_length = l if self.max_seq_length is None else self.max_seq_length
            assert min_length <= max_length
            if min_length == max_length:
                length = min_length
            else:
                length = np.random.randint(min_length, max_length, 1)[0]
            if length <= l:
                s_idx = np.random.randint(0, l - length + 1, 1)[0]
                e_idx = s_idx + length
            else:
                s_idx, e_idx = 0, l
        assert e_idx <= l, f'end of idx greater than l, e_idx={e_idx}, l={l}'

        # Call get_key_states() if you want to use the key states.
        # Here `s` is the state observation, `a` is the action, 
        # `env_states` not used during training (can be used to reconstruct env for debugging).
        # `t` is used for positional embedding as in Decision Transformer.
        data_dict = {
            's': self.data['obs'][index][s_idx:e_idx].astype(np.float32),
            'a': self.data['actions'][index][s_idx:e_idx].astype(np.float32),
            't': np.array([s_idx]).astype(np.float32),
            'unified_t': np.arange(start=s_idx, stop=e_idx, step=1.0, dtype=np.float32) / l
            # 'env_states': self.data['env_states'][index][s_idx:e_idx].astype(np.float32),
        }
        if self.with_key_states:
            if f'key_states_{index}' not in self.idx_to_key_states:
                self.idx_to_key_states[f'key_states_{index}'], self.idx_to_key_states_label[f'key_states_{index}'] \
                    = self.get_key_states(index)
            data_dict['k'], data_dict['k_label'] =\
                self.idx_to_key_states[f'key_states_{index}'],\
                self.idx_to_key_states_label[f'key_states_{index}'][s_idx:e_idx].astype(np.int32)
        # for k, v in data_dict.items():
        #     print(k, v.shape)
        return data_dict

    def info(self):  # Get observation and action shapes.
        return self.data['obs'][0].shape[-1], self.data['actions'][0].shape[-1]

    def load_demo_dataset(self, path, length):  
        dataset = {}
        traj_all = h5py.File(path)
        if length == -1:
            length = len(traj_all)
        np.random.seed(self.seed)  # Fix the random seed for train/test data split.

        # Since TurnFaucet-v0 uses 10 different faucet models, we shuffle the data
        # such that the resulting sampled data are evenly sampled across faucet models.
        if self.task == 'TurnFaucet-v0':
            ids = []
            for i in range(10):  # Hard-code the 10 data splits for permutation.
                t_ids = np.random.permutation(len(traj_all)//10)[:length//10]
                t_ids += i * len(traj_all) // 10
                ids.append(t_ids)
            ids = np.concatenate(ids)
        # Since PushChair uses 5 different faucet models, we shuffle the data
        # such that the resulting sampled data are evenly sampled across chair models.
        elif self.task == 'PushChair-v1':
            ids = []
            for i in range(5):  # Hard-code the 5 data splits for permutation.
                t_ids = np.random.permutation(len(traj_all)//5)[:length//5]
                t_ids += i*len(traj_all)//5
                ids.append(t_ids)
            ids = np.concatenate(ids)
        else:
            ids = np.random.permutation(len(traj_all))[:length]

        ids = ids.tolist() * self.multiplier  # Duplicate the data for faster loading.

        # Note that the size of `env_states` and `obs` is that of the others + 1.
        # And most `infos` is for the next obs rather than the current obs.

        # `env_states` is used for reseting the env (might be helpful for eval)
        dataset['env_states'] = [np.array(
            traj_all[f"traj_{i}"]['env_states']) for i in ids]
        # `obs` is the observation of each step.
        # print('env_states:', len(dataset['env_states']), dataset['env_states'][0].shape, dataset['env_states'][1].shape)

        dataset['obs'] = [np.array(traj_all[f"traj_{i}"]["obs"]) for i in ids]
        # print('obs:', len(dataset['obs']), dataset['obs'][0].shape, dataset['obs'][1].shape)

        dataset['actions'] = [np.array(traj_all[f"traj_{i}"]["actions"]) for i in ids]
        # print('actions:', len(dataset['actions']), dataset['actions'][0].shape, dataset['actions'][1].shape)
        
        # actions = np.concatenate(dataset['actions'])
        # actions_std = np.std(actions, 0)
        # dataset['actions'] = [
        #    np.array(traj_all[f"traj_{i}"]["actions"]) / (actions_std + 1e-7) for i in ids]

        # `rewards` is not currently used in CoTPC training.
        dataset['rewards'] = [np.array(traj_all[f"traj_{i}"]["rewards"]) for i in ids] 
        for k in traj_all['traj_0']['infos'].keys():
            dataset[f'infos/{k}'] = [np.array(
                traj_all[f"traj_{i}"]["infos"][k]) for i in ids]
            if k == 'info':  # For PushChair.
                for kk in traj_all['traj_0']['infos'][k].keys():
                    dataset[f'infos/demo_{kk}'] = [np.array(
                        traj_all[f"traj_{i}"]["infos"][k][kk]) for i in ids]

            # print(f'infos/{k}', len(dataset[f'infos/{k}']), dataset[f'infos/{k}'][0], dataset[f'infos/{k}'][1])

        self.max_steps = np.max([len(s) for s in dataset['env_states']])
        # the max_steps is in the aspect of states
        # (action + 1)
        
        return dataset

    def get_key_states(self, idx):
        # Note that `infos` is for the next obs rather than the current obs.
        # Thus, we need to offset the `step_idx`` by one.
        key_states = []
        key_states_idx = []

        # If TurnFaucet-v0 (two key states)
        # key state I: is_contacted -> true
        # key state II: end of the trajectory
        if self.task == 'TurnFaucet-v0':
            for step_idx, key in enumerate(self.data['infos/is_contacted'][idx]):
                if key: break
            key_states.append(self.data['obs'][idx][step_idx + 1].astype(np.float32))
            key_states_idx.append(step_idx + 1)

        # If PegInsertion (three key states)
        # key state I: is_grasped -> true
        # key state II: pre_inserted -> true
        # key state III: end of the trajectory
        if self.task == 'PegInsertionSide-v0':
            for step_idx, key in enumerate(self.data['infos/is_grasped'][idx]):
                if key: break
            key_states.append(self.data['obs'][idx][step_idx+1].astype(np.float32))
            key_states_idx.append(step_idx + 1)
            for step_idx, key in enumerate(self.data['infos/pre_inserted'][idx]):
                if key: break
            key_states.append(self.data['obs'][idx][step_idx+1].astype(np.float32))
            key_states_idx.append(step_idx + 1)
        
        # If PickCube (two key states)
        # key state I: is_grasped -> true
        # key state II: end of the trajectory
        if self.task == 'PickCube-v0':
            for step_idx, key in enumerate(self.data['infos/is_grasped'][idx]):
                if key: break
            key_states.append(self.data['obs'][idx][step_idx+1].astype(np.float32))
            key_states_idx.append(step_idx + 1)
        
        # If StackCube (three key states)
        # key state I: is_cubaA_grasped -> true
        # key state II: the last state of is_cubeA_on_cubeB -> true 
        #               right before is_cubaA_grasped -> false
        # key state III: end of the trajectory
        if self.task == 'StackCube-v0':
            for step_idx, key in enumerate(self.data['infos/is_cubaA_grasped'][idx]):
                if key: break
            key_states.append(self.data['obs'][idx][step_idx+1].astype(np.float32))
            key_states_idx.append(step_idx + 1)
            for step_idx, k1 in enumerate(self.data['infos/is_cubeA_on_cubeB'][idx]):
                k2 = self.data['infos/is_cubaA_grasped'][idx][step_idx]
                if k1 and not k2: break
            # Right before such a state and so we do not use step_idx+1.
            key_states.append(self.data['obs'][idx][step_idx].astype(np.float32))
            key_states_idx.append(step_idx)

        # If PushChair (four key states):
        # key state I: right before demo_rotate -> true
        # key state II: right before demo_move -> true
        # key state III: when chair_close_to_target & chair_standing -> true
        # key state IV: end of the trajectory
        lengths = []
        # In PushChair, demo_* indicate the current state (not the next). 
        if self.task == 'PushChair-v1':
            for step_idx, key in enumerate(self.data['infos/demo_rotate'][idx]):
                if key: break
            lengths.append(step_idx)
            key_states.append(self.data['obs'][idx][step_idx].astype(np.float32))
            key_states_idx.append(step_idx)
            for step_idx, key in enumerate(self.data['infos/demo_move'][idx]):
                if key: break
            lengths.append(step_idx - np.sum(lengths))
            key_states.append(self.data['obs'][idx][step_idx].astype(np.float32))
            key_states_idx.append(step_idx)
            for step_idx, key in enumerate(np.bitwise_and(
                    self.data['infos/chair_close_to_target'][idx],
                    self.data['infos/chair_standing'][idx])):
                if key: break
            lengths.append(step_idx + 1 - np.sum(lengths))
            key_states.append(self.data['obs'][idx][step_idx+1].astype(np.float32))
            key_states_idx.append(step_idx + 1)
            lengths.append(len(self.data['infos/success'][idx]) - np.sum(lengths))

        # Always append the last state in the trajectory as the last key state.
        key_states.append(self.data['obs'][idx][-1].astype(np.float32))
        key_states_idx.append(len(self.data['obs'][idx]) - 1)
        # print(key_states_idx)
        key_states_label = stepfunctionlist(np.array(key_states_idx))
        # print(key_states_label)

        key_states = np.stack(key_states, 0).astype(np.float32)
        assert len(key_states) > 0, self.task
        return key_states, key_states_label


# To obtain the padding function for sequences.
def get_padding_fn(data_names):
    assert 's' in data_names, 'Should at least include `s` in data_names.'

    def pad_collate(*args):
        assert len(args) == 1
        output = {k: [] for k in data_names}
        for b in args[0]:  # Batches
            for k in data_names:
                output[k].append(torch.from_numpy(b[k]))

        # Include the actual length of each sequence sampled from a trajectory.
        # If we set max_seq_length=min_seq_length, this is a constant across samples.
        output['lengths'] = torch.tensor([len(s) for s in output['s']])

        # Padding all the sequences.
        for k in data_names:
            output[k] = pad_sequence(output[k], batch_first=True, padding_value=0)

        return output

    return pad_collate
    

# Sample code for the data loader.
if __name__ == "__main__":

    from torch.utils.data import DataLoader
    
    # The default values for CoTPC for tasks in ManiSkill2.
    batch_size, num_traj, seed, min_seq_length, max_seq_length, task = \
        256, 500, 0, 1, 4, 'PegInsertionSide-v0'
    # batch_size, num_traj, seed, min_seq_length, max_seq_length, task = \
    #     256, 500, 0, 60, 60, 'PushChair-v1'

    train_dataset = MS2Demos(
        # control_mode='pd_joint_delta_pos', 
        control_mode='pd_joint_delta_pos',
        length=num_traj, seed=seed,
        min_seq_length=min_seq_length, 
        max_seq_length=max_seq_length,
        with_key_states=True,
        task=task)

    collate_fn = get_padding_fn(['s', 'a', 't', 'unified_t', 'k', 'k_label'])
    train_data = DataLoader(
        dataset=train_dataset, 
        batch_size=4,  # batch_size,
        collate_fn=collate_fn)

    data_iter = iter(train_data)
    data = next(data_iter)
    # print(data.keys())
    # print(len(data))  # 4  
    for k, v in data.items():
        if k in ['s', 'a', 'lengths']:
            print(k)
            print(v[0])
            print(v[1])
            print(v[2])
            print(v[3])

    data = next(data_iter)
    # print(data.keys())
    # print(len(data))  # 4
    for k, v in data.items():
        if k in ['s', 'a', 'lengths']:
            print(k)
            print(v.shape)
            print(v[0])
            print(v[1])
            print(v[2])
            print(v[3])