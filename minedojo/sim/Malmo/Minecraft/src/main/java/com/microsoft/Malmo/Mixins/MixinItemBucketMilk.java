package com.microsoft.Malmo.Mixins;

import net.minecraft.item.ItemBucketMilk;
import net.minecraft.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;


@Mixin(ItemBucketMilk.class)
public class MixinItemBucketMilk{

    @Overwrite
    public int getMaxItemUseDuration(ItemStack item)
    {
        return 1;
    }
}
