package com.microsoft.Malmo.Mixins;

import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.inventory.Container;
import net.minecraft.inventory.ContainerPlayer;
import net.minecraft.inventory.Slot;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.TreeSet;

@Mixin(ContainerPlayer.class)
public abstract class MixinLargeInventorySlots extends Container {
    @Inject(method="<init>*", at=@At("RETURN"))
    public void constructorTail(CallbackInfo ci) {
        InventoryPlayer inventory = null;
        TreeSet<Integer> missingIndices = new TreeSet<Integer>();
        for (Slot slot : this.inventorySlots) {
            if (slot.inventory instanceof InventoryPlayer) {
                if (inventory == null) {
                    inventory = (InventoryPlayer) slot.inventory;
                    for (int i = 0; i < inventory.mainInventory.size(); i++) {
                        missingIndices.add(i);
                    }
                }
                if (slot.slotNumber >= 36) {
                    // These are armor and other equipment slots, we shift their indices by 360 - 36 since we've
                    // expanded the previous 36-long inventory to 360.
                    slot.slotNumber += inventory.mainInventory.size() - 36;
                }
                else {
                    missingIndices.remove(slot.slotNumber);
                }
            }
        }
        if (inventory == null) {
            // TODO: should raise an error?
            return;
        }
        while (missingIndices.size() > 0) {
            int slot = missingIndices.first();
            // Note: the first "slot" is the actual index, the other two are what the x and y position should be in the
            // UI, which does not make sense in our case so we just pass "slot" instead (any other integer should
            // do the trick too, but passing slot just in case there is any issue with having two slots with the
            // same x-y position).
            this.addSlotToContainer(new Slot(inventory, slot, slot, slot));
            missingIndices.remove(slot);
        }
    }
}
