import minedojo

env = minedojo.make(
    task_id="playthrough",
    image_size=(160, 256)
)
obs = env.reset()
for i in range(1000):
    act = env.action_space.no_op()
    obs, reward, done, info = env.step(act)
env.close()
