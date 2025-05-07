import pickle

from algorithm.discor.replay_buffer import ReplayBuffer

# Create empty ReplayBuffer
buffer = ReplayBuffer(
    capacity=8000000,  # Must match the training config (this is from your logs)
    nstep=3,           # Must match training config
    gamma=0.992        # Must match training config
)

# Save it to replay_buffer.pkl
with open("replay_buffer.pkl", "wb") as f:
    pickle.dump(buffer, f)

print("Empty replay_buffer.pkl created.")