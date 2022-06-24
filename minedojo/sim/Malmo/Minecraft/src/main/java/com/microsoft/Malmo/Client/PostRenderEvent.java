package com.microsoft.Malmo.Client;

import net.minecraftforge.fml.common.eventhandler.Event;

public class PostRenderEvent extends Event {
    private float partialTicks;

    public PostRenderEvent(float partialTicks) {
        this.partialTicks = partialTicks;
    }

    public float getPartialTicks() {
        return partialTicks;
    }
}
