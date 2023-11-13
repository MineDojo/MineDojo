import minedojo


if __name__ == "__main__":
    env = minedojo.make(
        task_id="open-ended",
        image_size=(288, 512),
        world_seed=32,
        seed=42,
    )

    #print(f"[INFO] Create a task with prompt: {env.task_prompt}")

    env.reset()
    for _ in range(1000):
        obs, reward, done, info = env.step(env.action_space.sample())
    env.close()

    print("[INFO] Installation Success")
