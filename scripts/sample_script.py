import minedojo

env = minedojo.make(task_id="playthrough",image_size=(640, 1024))

obs = env.reset()

#next_obs, reward, done, info = env.step(action)

num_steps_you_want_to_run=1000
save_path="./playthrough.mp4"
fps=25

# some setup
rgb_list = []

for _ in range(num_steps_you_want_to_run):
    # get actions
    obs, reward, done, info = env.step(action)
    rgb_list.append(obs["rgb"])
rgbs = np.stack(rgb_list)
rgbs = torch.from_numpy(rgbs)
torchvision.io.write_video(save_path, rgbs, fps=fps)

env.close()
