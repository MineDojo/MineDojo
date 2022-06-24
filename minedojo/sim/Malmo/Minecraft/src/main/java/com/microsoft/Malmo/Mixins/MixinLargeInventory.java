package com.microsoft.Malmo.Mixins;


import java.util.Random;

import com.microsoft.Malmo.Utils.SeedHelper;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.item.ItemStack;
import net.minecraft.util.NonNullList;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;


@Mixin(InventoryPlayer.class)
public abstract class MixinLargeInventory  {
    // /* Overrides default inventory size within the InventoryPlayer class.
    //  */
    @Final public final NonNullList<ItemStack> mainInventory = NonNullList.<ItemStack>withSize(360, ItemStack.EMPTY);
}
