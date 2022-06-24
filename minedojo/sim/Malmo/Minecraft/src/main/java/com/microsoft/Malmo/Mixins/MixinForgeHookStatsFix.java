package com.microsoft.Malmo.Mixins;

import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraftforge.common.ForgeHooks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(ForgeHooks.class)
public abstract class MixinForgeHookStatsFix {
    @Redirect(method = "onPlaceItemIntoWorld",
              at = @At(
                      value = "INVOKE",
                      target = "net/minecraft/item/ItemStack.getItem ()Lnet/minecraft/item/Item;",
                      ordinal = 2
              )
    )
    private static Item correctlyGetItem(ItemStack itemstack){
        int prevCount = itemstack.getCount();
        itemstack.setCount(1);
        Item item = itemstack.getItem();
        itemstack.setCount(prevCount);
        return item;
    }
}
