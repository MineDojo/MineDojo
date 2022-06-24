package com.microsoft.Malmo.Mixins;

import com.microsoft.Malmo.Client.MalmoModClient;
import com.microsoft.Malmo.MalmoMod;
import net.minecraft.block.*;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.client.multiplayer.PlayerControllerMP;
import net.minecraft.client.multiplayer.WorldClient;
import net.minecraft.entity.Entity;
import net.minecraft.entity.item.EntityMinecartCommandBlock;
import net.minecraft.entity.item.EntityMinecartContainer;
import net.minecraft.entity.item.EntityMinecartFurnace;
import net.minecraft.entity.passive.EntityCow;
import net.minecraft.entity.passive.EntityVillager;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.item.Item;
import net.minecraft.item.ItemBook;
import net.minecraft.item.ItemSign;
import net.minecraft.util.EnumActionResult;
import net.minecraft.util.EnumFacing;
import net.minecraft.util.EnumHand;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.RayTraceResult;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import org.spongepowered.asm.mixin.injection.callback.LocalCapture;
import org.spongepowered.asm.mixin.injection.struct.MemberInfo;

import java.util.logging.Level;
import java.util.logging.Logger;

@Mixin(PlayerControllerMP.class)
public abstract class MixinNoGuiInteract {
    private void catchGuiEntity(Entity target, CallbackInfoReturnable<EnumActionResult> cir) {
        if (MalmoMod.isLowLevelInput()) {
            return;
        }
        if (target instanceof EntityVillager
                || target instanceof EntityMinecartContainer
                || target instanceof EntityMinecartFurnace
                || target instanceof EntityMinecartCommandBlock){
            cir.setReturnValue(EnumActionResult.SUCCESS);
            cir.cancel();
        }
    }

    private void catchGuiItem(Item target, CallbackInfoReturnable<EnumActionResult> cir) {
        if (MalmoMod.isLowLevelInput()) {
            return;
        }
        if (target instanceof ItemSign
            || target instanceof ItemBook) {
            cir.setReturnValue(EnumActionResult.PASS);
            cir.cancel();
        }
    }

    /**
     * Disable USE interactions with EntityVillager, MinecartContainers (EntityMinecartChest, EntityMinecartHopper) and EntityMinecartCommandBlock
     * This prevents the server from bing notified that we tried to interact with these entities
     * @param player
     * @param target
     * @param heldItem
     * @param cir
     */
    @Inject(method = "interactWithEntity(Lnet/minecraft/entity/player/EntityPlayer;Lnet/minecraft/entity/Entity;Lnet/minecraft/util/EnumHand;)Lnet/minecraft/util/EnumActionResult;",at = @At("HEAD"), cancellable = true)
    private void onInteractWithEntity(EntityPlayer player, Entity target, EnumHand heldItem, CallbackInfoReturnable<EnumActionResult> cir) {
        catchGuiEntity(target, cir);
    }

    @Inject(method = "interactWithEntity(Lnet/minecraft/entity/player/EntityPlayer;Lnet/minecraft/entity/Entity;Lnet/minecraft/util/math/RayTraceResult;Lnet/minecraft/util/EnumHand;)Lnet/minecraft/util/EnumActionResult;", at = @At("HEAD"), cancellable = true)
    private void onInteractWithEntity2(EntityPlayer player, Entity target, RayTraceResult result, EnumHand heldItem, CallbackInfoReturnable<EnumActionResult> cir) {
        catchGuiEntity(target, cir);
    }


    @Inject(method = "processRightClickBlock", at = @At("HEAD"), cancellable = true)
    private void onProcessRightClickBlock(EntityPlayerSP player, WorldClient worldIn, BlockPos stack, EnumFacing pos, Vec3d facing, EnumHand vec, CallbackInfoReturnable<EnumActionResult> cir) {
        if (MalmoMod.isLowLevelInput()) {
            return;
        }
        Block block = worldIn.getBlockState(stack).getBlock();
        if (block instanceof BlockContainer
        || block instanceof BlockAnvil
        || block instanceof BlockWorkbench) {
            cir.setReturnValue(EnumActionResult.PASS);
            cir.cancel();
        }
        catchGuiItem(player.getHeldItem(vec).getItem(), cir);
    }

    @Inject(method = "processRightClick", at = @At("HEAD"), cancellable = true)
    private void onProcessRightClick(EntityPlayer player, World worldIn, EnumHand stack, CallbackInfoReturnable<EnumActionResult> cir) {
        catchGuiItem(player.getHeldItem(stack).getItem(), cir);
    }
}