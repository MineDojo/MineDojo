package com.microsoft.Malmo.Mixins;

import net.minecraft.item.ItemFood;
import net.minecraft.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;


@Mixin(ItemFood.class)
public abstract class MixinItemFood{

    public int itemUseDuration = 1;

    @Overwrite
    public int getMaxItemUseDuration(ItemStack item)
    {
        return 1;
    }
}
