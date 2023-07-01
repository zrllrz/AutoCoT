"""
Code for the module architecture of CoTPC, based on the GPT implementation.
Some of the key hyper-parameters are explained in GPTConfig.

References:
(1) https://github.com/karpathy/minGPT
(2) https://github.com/kzl/decision-transformer
"""

import math
import torch
import torch.nn as nn
from torch.nn import functional as F
import numpy as np


class MLP(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dims=[], act_fn='relu'):
        super().__init__()
        assert act_fn in ['relu', 'tanh', None, '']
        dims = [input_dim] + hidden_dims + [output_dim]
        layers = []
        for i, j in zip(dims[:-1], dims[1:]):
            layers.append(nn.Linear(i, j))
            if act_fn == 'relu':
                layers.append(nn.ReLU())
            if act_fn == 'tanh':
                layers.append(nn.Tanh())
        self.net = nn.Sequential(*layers[:-1])

    def forward(self, x):
        return self.net(x)


class GELU(nn.Module):
    def forward(self, input):
        return F.gelu(input)


class GPTConfig:
    """ base GPT config, params common to all GPT versions """

    embd_pdrop = 0.0
    resid_pdrop = 0.0
    attn_pdrop = 0.0

    def __init__(self, block_size, **kwargs):
        assert kwargs['model_type'] in ['s', 's+a', 's+cot', 's+a+cot'], \
            f"Unsupported model_type: {kwargs['model_type']}"

        if '+a' in kwargs['model_type']:  # If the action history is used.
            self.block_size = block_size * 2
        else:
            self.block_size = block_size

        if 'cot' in kwargs['model_type']:
            # `key_states` specifies which of the key states should be used for CoT.
            assert 'key_states' in kwargs, 'Should specify `key_states`'
            # It is in the form of 'acd...' that represents whether the key
            # state x is used. e.g., here a,c,d is used while b is skipped.
            assert kwargs['key_states'] not in ['', None] and \
                   np.all([ord('z') >= ord(g) >= ord('a') for g in kwargs['key_states']])

            # `key_state_loss` specifies which layer's features in GPT should be used
            # for for the auxiliary key state prediction losses.
            assert 'key_state_loss' in kwargs, 'Should specify `key_state_loss`'
            # It is in the form of e.g., '023', meaning the features out of attention
            # layers of idx 0, 2, 3 are used for key state prediction losses.
            assert kwargs['key_state_loss'] not in ['', None] and \
                   np.all([l.isnumeric() for l in kwargs['key_state_loss']])

            self.key_states = kwargs['key_states']
            self.key_state_loss = kwargs['key_state_loss']
            self.len_key_states = len(kwargs['key_states'])
        else:
            self.len_key_states = 0

        # Set up other attributes.
        for k, v in kwargs.items():
            setattr(self, k, v)


class CausalSelfAttentionWithCoT(nn.Module):
    """
    A multi-head masked self-attention layer equipped with key state query tokens for
    chain-of-thought predictive control. It is adapted from the minGPT repo.
    """

    def __init__(self, config):
        super().__init__()
        assert config.n_embd % config.n_head == 0

        # key, query, value projections for all heads
        self.key = nn.Linear(config.n_embd, config.n_embd)
        self.query = nn.Linear(config.n_embd, config.n_embd)
        self.value = nn.Linear(config.n_embd, config.n_embd)

        # regularization
        self.attn_drop = nn.Dropout(config.attn_pdrop)
        self.resid_drop = nn.Dropout(config.resid_pdrop)

        # output projection
        self.proj = nn.Linear(config.n_embd, config.n_embd)

        # causal mask to ensure that attention is only applied to the left in the input sequence
        block_size = config.block_size + config.len_key_states
        self.register_buffer("mask",
                             torch.tril(torch.ones(block_size, block_size)).view(1, 1, block_size, block_size))

        self.n_head = config.n_head
        self.model_type = config.model_type
        self.len_key_states = config.len_key_states

        # For the learnable key state query tokens, they are actually all-to-all, meaning
        # they can access to all future tokens during inference, and up to a future step
        # randomly selected during training (see `key_state_mask` in forward(...)).
        self.mask[:, :, :self.len_key_states] = 1.0

    def forward(self, x, key_state_mask=None):
        B, T, C = x.size()

        # calculate query, key, values for all heads in batch and move head forward to be the batch dim
        k = self.key(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)  # (B, nh, T, hs)
        q = self.query(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)  # (B, nh, T, hs)
        v = self.value(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)  # (B, nh, T, hs)

        # causal self-attention; Self-attend: (B, nh, T, hs) x (B, nh, hs, T) -> (B, nh, T, T)
        att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
        att = att.masked_fill(self.mask[:, :, :T, :T] == 0, float('-inf'))  # Masked attention

        # Masks used for the learnable key state query tokens, which are not causal (auto-regressive).
        if 'cot' in self.model_type:
            assert key_state_mask is not None
            att = att.masked_fill(key_state_mask, float('-inf'))

        att = F.softmax(att, dim=-1)
        att = self.attn_drop(att)
        y = att @ v  # (B, nh, T, T) x (B, nh, T, hs) -> (B, nh, T, hs)
        y = y.transpose(1, 2).contiguous().view(B, T, C)  # re-assemble all head outputs side by side

        # output projection
        y = self.resid_drop(self.proj(y))
        return y


class Block(nn.Module):
    """
    A Transformer block with masks specified for the learnable key state query tokens.
    """

    def __init__(self, config):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.n_embd)
        self.ln2 = nn.LayerNorm(config.n_embd)
        self.attn = CausalSelfAttentionWithCoT(config)
        self.mlp = nn.Sequential(
            nn.Linear(config.n_embd, 4 * config.n_embd),
            GELU(),
            nn.Linear(4 * config.n_embd, config.n_embd),
            nn.Dropout(config.resid_pdrop),
        )

    def forward(self, x, key_state_mask=None):
        x = x + self.attn(self.ln1(x), key_state_mask=key_state_mask)
        x = x + self.mlp(self.ln2(x))
        return x


class BlocksWithCoT(nn.Module):
    """
    A wrapper class for a sequence of Transformer blocks with masks specified for
    the learnable key state query tokens.
    """

    def __init__(self, config):
        super().__init__()
        # Register all the individual blocks.
        self.block_list = nn.ModuleList(Block(config) for _ in range(config.n_layer))
        self.model_type = config.model_type
        self.n_head = config.n_head
        self.len_key_states = config.len_key_states

    def forward(self, x, key_state_mask=None, intermediate_feats=None):
        B, T, _ = x.shape

        # During training the `key_state_mask` is not specified and we apply random
        # masking such that the first t tokens after the key state query tokens are
        # 0's and otherwise 1's, where t is uniformly sampled from 0 to traj length.
        # Here 1's mean no attention over the underlying masked tokens.
        # During inference, the evaluator should specify key state masks.
        if key_state_mask is None:
            # If use both state and action history,
            # make sure masks for s and a has the same length.
            if '+a' in self.model_type:
                r = torch.randint(0, (T - self.len_key_states) // 2, [B])[:, None] * 2
            else:
                r = torch.randint(0, T - self.len_key_states, [B])[:, None]
            # When '+a', we always ignore the last action token (set mask=1).
            mask = torch.arange(0, T).repeat(B, 1) > r + self.len_key_states
            key_state_mask = torch.zeros([B, self.n_head, T, T], dtype=torch.bool, device=x.device)
            key_state_mask[:, :, :self.len_key_states, :] = \
                mask[:, None, None, :].repeat(1, self.n_head, self.len_key_states, 1)

        output = []  # Also keep the intermediate results.

        skip_begin = None
        skip_end = None
        use_skip = intermediate_feats is not None
        if use_skip is True:
            skip_begin = 1
            skip_end = min(len(intermediate_feats) + 1, len(self.block_list))

        i_int_feat = 0
        for i_layer, block in enumerate(self.block_list):
            if use_skip is True and skip_begin <= i_layer < skip_end:
                # USELESS CAN DELETE
                x[:, -intermediate_feats[i_int_feat].shape[1]:, ...] \
                    = x[:, -intermediate_feats[i_int_feat].shape[1]:, ...] + intermediate_feats[i_int_feat]
                x = block(x, key_state_mask=key_state_mask)
                i_int_feat += 1
            else:
                x = block(x, key_state_mask=key_state_mask)
            output.append(x)

        return x, output


class KeyNet(nn.Module):
    """
    GPT Encoder, to encoder s,a sequence into key states
    So it is always without cot...
    """
    def __init__(self, config, state_dim=-1, action_dim=-1):
        super().__init__()

        assert state_dim > 0 and action_dim > 0
        self.config = config
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.use_skip_connection = config.use_skip_connection  # USELESS CAN DELETE
        self.model_type = config.model_type
        self.block_size = config.block_size
        assert 'cot' not in config.model_type, 'Again, we do not receive cot input in KeyNet'

        p_size = config.block_size // 2 if '+a' in self.model_type else config.block_size
        self.local_pos_emb = nn.Parameter(torch.zeros(1, p_size, config.n_embd))
        self.global_pos_emb = nn.Parameter(
            torch.zeros(1, config.max_timestep, config.n_embd))

        self.drop = nn.Dropout(config.embd_pdrop)

        # Transformer (attention layers) with CoT.
        self.blocks = BlocksWithCoT(config)

        # State embeddings.
        self.state_encoder = MLP(self.state_dim, config.n_embd, hidden_dims=[256])

        # Action embeddings.
        if '+a' in self.model_type:
            self.action_encoder = MLP(self.action_dim, config.n_embd, hidden_dims=[256])

        self.ln = nn.LayerNorm(config.n_embd)
        # Do not need predictor...
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    # Given state (and action) history, predict actions (and key states as CoT).
    # `timesteps` is used for the global+local position embedding design similar
    # to the one in Decision Transformer. `key_state_mask` is used so that the
    # (all-to-all) key state query tokens can attend to later tokens.
    def forward(self, states, timesteps, actions=None):
        B, T = states.shape[0], states.shape[1]
        state_embeddings = self.state_encoder(states)

        # Embeddings for state (action, and key state query) tokens.
        token_embeddings = torch.zeros([B, self.block_size, self.config.n_embd],
                                       dtype=torch.float32, device=states.device)

        # If using action history as inputs: during training, all actions are
        # specified; during inference, only actions in the past are specified.
        # That is, the first action prediction has no action history as inputs.
        if '+a' in self.model_type:
            token_embeddings[:, :T * 2:2, :] = state_embeddings

            if actions is not None:
                # Assume the last action is not used as inputs during training.
                action_embeddings = self.action_encoder(actions[:, :T - 1])
                token_embeddings[:, 1:T * 2 - 1:2, :] = action_embeddings

        else:
            token_embeddings[:, :T, :] = state_embeddings

        # Set up position embeddings similar to that in Decision Transformer.
        global_pos_emb = torch.repeat_interleave(self.global_pos_emb, B, dim=0)
        timesteps_rp = torch.repeat_interleave(timesteps[:, None], self.config.n_embd, dim=-1)
        global_pos_emb = torch.gather(
            global_pos_emb, 1, timesteps_rp.long())  # BS x 1 x D
        local_pos_emb = torch.repeat_interleave(self.local_pos_emb, 2, dim=1) \
            if '+a' in self.model_type else self.local_pos_emb

        x = token_embeddings + global_pos_emb + local_pos_emb

        key_emb = self.drop(x)
        key_emb, intermediate_feats = self.blocks(key_emb)
        key_emb = self.ln(key_emb)

        # We now only use the last state as key state embedding feature
        # Also, we can use the embedded states and action, namely the initial x
        # And the states number T
        if self.use_skip_connection:
            return key_emb, x, T, intermediate_feats[:-1]
        else:
            return key_emb, x, T, None


class ActNet(nn.Module):
    """
    GPT Decoder, to decode key_state_prompt, s,a sequence into action prediction
    So it is always with cot
    """

    def __init__(self, config, state_dim=-1, action_dim=-1):
        super().__init__()

        assert state_dim > 0 and action_dim > 0
        self.config = config
        self.state_dim = state_dim
        self.action_dim = action_dim

        assert 'cot' in config.model_type
        self.model_type = config.model_type
        self.key_states = config.key_states
        self.len_key_states = config.len_key_states
        self.block_size = config.block_size

        # We must have cot!!!
        # We do not need key_state_pos_emb for our output from keynet is trying to do it
        # self.key_state_pos_emb = nn.Parameter(
        #     torch.zeros(1, self.len_key_states, config.n_embd))

        # Transformer (attention layers) with CoT.
        self.blocks = BlocksWithCoT(config)

        # No state and action embeddings

        # Action predictor.
        self.ln = nn.LayerNorm(config.n_embd)
        self.action_predictor = MLP(config.n_embd, action_dim, hidden_dims=[256, 256])

        # Still do not need key state predictor for we do not need the output of key states

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    def forward(self, key_emb_out, x, T, intermediate_feats=None, key_state_mask=None):
        x = torch.cat([key_emb_out, x], 1)
        x, intermediate_feats = self.blocks(
            x=x,
            key_state_mask=key_state_mask,
            intermediate_feats=intermediate_feats
        )
        x = self.ln(x)
        act_preds = self.action_predictor(x)

        act_preds = torch.split(act_preds, [self.len_key_states, self.block_size], dim=1)[1]

        # Get rid of dims for action tokens.
        if '+a' in self.model_type:
            # Remove the extra tokens when in eval mode.
            act_preds = act_preds[:, :T * 2:2]

        # Only have act_preds output
        return act_preds


class RecNet(nn.Module):
    """
    GPT Decoder, to decode all key_states, back to states
    """
    def __init__(self, config, state_dim=-1, action_dim=-1):
        super().__init__()

        assert state_dim > 0 and action_dim > 0
        self.config = config
        self.state_dim = state_dim
        self.action_dim = action_dim

        # We only need key states feature to
        assert 'cot' not in config.model_type and '+a' not in config.model_type
        self.model_type = config.model_type
        self.len_key_states = config.len_key_states
        self.block_size = config.block_size

        # We do not need key_state_pos_emb for our output from keynet is trying to do it

        # Transformer (attention layers) with CoT.
        self.blocks = BlocksWithCoT(config)

        # No state and action embeddings

        # Action predictor.
        self.ln = nn.LayerNorm(config.n_embd)
        self.states_predictor = MLP(config.n_embd, state_dim, hidden_dims=[256, 256])

        # Still do not need key state predictor for we do not need the output of key states

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    def forward(self, key_emb, T):
        x = key_emb
        x, intermediate_feats = self.blocks(x=x)
        x = self.ln(x)
        state_recs = self.states_predictor(x)

        # Only have act_preds output
        return state_recs[:, :T]
