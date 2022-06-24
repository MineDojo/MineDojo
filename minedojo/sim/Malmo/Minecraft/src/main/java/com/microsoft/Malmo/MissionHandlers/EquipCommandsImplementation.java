// --------------------------------------------------------------------------------------------------
//  Copyright (c) 2016 Microsoft Corporation
//  
//  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
//  associated documentation files (the "Software"), to deal in the Software without restriction,
//  including without limitation the rights to use, copy, modify, merge, publish, distribute,
//  sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
//  furnished to do so, subject to the following conditions:
//  
//  The above copyright notice and this permission notice shall be included in all copies or
//  substantial portions of the Software.
//  
//  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
//  NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
//  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
//  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
// --------------------------------------------------------------------------------------------------

package com.microsoft.Malmo.MissionHandlers;

import com.microsoft.Malmo.Utils.MineRLTypeHelper;

import com.microsoft.Malmo.MalmoMod;
import com.microsoft.Malmo.Schemas.*;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.entity.EntityLiving;
import net.minecraft.init.Blocks;
import net.minecraft.init.Items;
import net.minecraft.inventory.EntityEquipmentSlot;

import net.minecraftforge.fml.common.network.simpleimpl.IMessage;
import net.minecraftforge.fml.common.network.simpleimpl.IMessageHandler;
import net.minecraftforge.fml.common.network.simpleimpl.MessageContext;

/**
 * @author Brandon Houghton, Carnegie Mellon University
 * <p>
 * Equip commands allow agents to equip any item in their inventory worry about slots or hotbar location.
 */
public class EquipCommandsImplementation extends CommandBase {
    private boolean isOverriding;

    public static class EquipMessageHandler
            implements IMessageHandler<MineRLTypeHelper.ItemTypeMetadataMessage, IMessage> {
        @Override
        public IMessage onMessage(MineRLTypeHelper.ItemTypeMetadataMessage message, MessageContext ctx) {
            EntityPlayerMP player = ctx.getServerHandler().playerEntity;
            if (player == null)
                return null;

            Item item = Item.getByNameOrId(message.getItemType());

            InventoryPlayer inv = player.inventory;
            Integer matchIdx = MineRLTypeHelper.inventoryIndexOf(inv, message.getItemType(), message.getMetadata());

            if (matchIdx != null) {
                EntityEquipmentSlot equipmentSlot = EntityLiving.getSlotForItemStack(new ItemStack(item));
                ItemStack stackInInventory = inv.getStackInSlot(matchIdx).copy();

                // Swap current hotbar item with found inventory item (if not the same)
                ItemStack prev = player.getItemStackFromSlot(equipmentSlot);
                player.setItemStackToSlot(equipmentSlot, stackInInventory);
                player.inventory.setInventorySlotContents(matchIdx, prev);
            }

            return null;
        }
    }

    @Override
    protected boolean onExecute(String verb, String parameter, MissionInit missionInit) {
        if (!verb.equalsIgnoreCase("equip")) {
            return false;
        }

        MineRLTypeHelper.ItemTypeMetadataMessage msg = new MineRLTypeHelper.ItemTypeMetadataMessage(parameter);
        if (msg.validateItemType()) {
            MalmoMod.network.sendToServer(msg);
        }
        return true;  // Packet is captured by equip handler
    }

    @Override
    public boolean parseParameters(Object params) {
        if (!(params instanceof EquipCommands))
            return false;

        EquipCommands pParams = (EquipCommands) params;
        // Todo: Implement allow and deny lists.
        // setUpAllowAndDenyLists(pParams.getModifierList());
        return true;
    }

    @Override
    public void install(MissionInit missionInit) {
    }

    @Override
    public void deinstall(MissionInit missionInit) {
    }

    @Override
    public boolean isOverriding() {
        return this.isOverriding;
    }

    @Override
    public void setOverriding(boolean b) {
        this.isOverriding = b;
    }
}
