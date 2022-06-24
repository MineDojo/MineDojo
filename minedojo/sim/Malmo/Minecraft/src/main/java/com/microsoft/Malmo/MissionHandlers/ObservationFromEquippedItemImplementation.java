package com.microsoft.Malmo.MissionHandlers;

import com.microsoft.Malmo.Utils.MineRLTypeHelper;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.inventory.EntityEquipmentSlot;
import net.minecraft.item.ItemStack;

import com.google.gson.JsonObject;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Schemas.MissionInit;
import org.jetbrains.annotations.Nullable;

/**
 * Simple IObservationProducer object that pings out a whole bunch of data.<br>
 */
public class ObservationFromEquippedItemImplementation extends HandlerBase implements IObservationProducer
{
	@Override
	public void prepare(MissionInit missionInit) {}

	@Override
	public void cleanup() {}

	@Override
    public void writeObservationsToJSON(JsonObject json, MissionInit missionInit)
    {
        json.add("equipped_items", getEquipmentJSON());
    }

    public static JsonObject getEquipmentJSON() {
        EntityPlayerSP player = Minecraft.getMinecraft().player;
        JsonObject equipment = new JsonObject();
        for(EntityEquipmentSlot slot : EntityEquipmentSlot.values()) {
            equipment.add(slot.getName(), getInventoryJson(player.inventory.getStackInSlot(slot.getSlotIndex())));
        }
        return equipment;
    }

    public static JsonObject getInventoryJson(@Nullable ItemStack itemToAdd){
            JsonObject jobj = new JsonObject();
            if (itemToAdd != null && !itemToAdd.isEmpty())
            {
                String type = MineRLTypeHelper.getItemType(itemToAdd.getItem());
                jobj.addProperty("type", type);
	              if (itemToAdd.getHasSubtypes()){
                    jobj.addProperty("metadata", itemToAdd.getMetadata());
	              } else {
                    jobj.addProperty("metadata", 0);
	              }
                jobj.addProperty("quantity", itemToAdd.getCount());
                if(itemToAdd.isItemStackDamageable()){
                    jobj.addProperty("currentDamage", itemToAdd.getItemDamage());
                    jobj.addProperty("maxDamage", itemToAdd.getMaxDamage());
                } else{
                    jobj.addProperty("currentDamage", -1);
                    jobj.addProperty("maxDamage", -1);
                }
            }
            return jobj;
    }
}
