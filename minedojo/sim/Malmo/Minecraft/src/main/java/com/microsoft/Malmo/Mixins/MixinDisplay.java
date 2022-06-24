package com.microsoft.Malmo.Mixins;

import org.lwjgl.opengl.Display;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;

@Mixin(Display.class)
public abstract class MixinDisplay {

    @Overwrite
    public static boolean isActive() {
        return true;
    }
}