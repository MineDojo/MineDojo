package com.microsoft.Malmo.Utils;

import com.google.gson.JsonObject;
import io.netty.buffer.ByteBuf;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.util.ResourceLocation;
import net.minecraftforge.fml.common.network.ByteBufUtils;
import net.minecraftforge.fml.common.network.simpleimpl.IMessage;
import org.jetbrains.annotations.Nullable;

public class MineRLTypeHelper {

    /**
     * @return A String item type suitable for Types.xsd or passing back to MineRL in messages, or
     *     null if such a String could not be found.
     */
    @Nullable
    public static String getItemType(Item item) {
        ResourceLocation resourceLocation = Item.REGISTRY.getNameForObject(item);
        if (resourceLocation == null) {
            return null;
        } else {
            return resourceLocation.getResourcePath();
        }
    }

    public static void writeItemStackToJson(ItemStack stack, JsonObject jsonObject) {
        int metadata = 0;
        if (stack.getHasSubtypes()){
            metadata = stack.getMetadata();
        }
        validateMetadata(metadata);
        jsonObject.addProperty("name", MineRLTypeHelper.getItemType(stack.getItem()));
        jsonObject.addProperty("variant", metadata);
        jsonObject.addProperty("quantity", stack.getCount());
        if(stack.isItemStackDamageable()){
            jsonObject.addProperty("max_durability", stack.getMaxDamage());
            jsonObject.addProperty("cur_durability", stack.getMaxDamage() - stack.getItemDamage());
        } else{
            jsonObject.addProperty("max_durability", -1);
            jsonObject.addProperty("cur_durability", -1);
        }
    }

    private static void validateMetadata(Integer metadata) {
        if (metadata == null) {
            return;
        }
    }

    /**
     * Find the lowest inventory index that matches the itemType and the metadata.
     * @param itemType The String name of the Item or ItemStack.
     * @param metadata The metadata or the damage of the ItemStack. Pass null to ignore this constraint.
     * @return The lowest inventory index matching the contraints, or null if no such slot is found.
     */
    @Nullable
    public static Integer inventoryIndexOf(InventoryPlayer inventory, String itemType, @Nullable Integer metadata) {
        Item parsedItem = Item.getByNameOrId(itemType);
        if (parsedItem == null || parsedItem.getRegistryName() == null)
            throw new IllegalArgumentException(itemType);
        ResourceLocation targetRegName = parsedItem.getRegistryName();

        if (metadata != null) {
            validateMetadata(metadata);
        }

        for (int i = 0; i < inventory.getSizeInventory(); i++) {
            ItemStack stack = inventory.getStackInSlot(i);
            ResourceLocation regName = stack.getItem().getRegistryName();
            if (regName == null) {
                System.out.printf("null RegistryName at inventory index %d%n", i);
                return null;
            }

            boolean flagItemTypeMatches = regName.equals(targetRegName);
            boolean flagItemMetadataMatches = (metadata == null) || (!stack.getHasSubtypes()) || (metadata == stack.getMetadata()) ;

            if (flagItemTypeMatches && flagItemMetadataMatches) {
                return i;
            }
        }
        return null;
    }

    public static class ItemTypeMetadataMessage implements IMessage {
        private String parameters;
        private String itemType;
        private Integer metadata;

        public ItemTypeMetadataMessage(){}

        public ItemTypeMetadataMessage(String parameters) {
            setParameters(parameters);
        }

        private void setParameters(String parameters) {
            this.parameters = parameters;

            String[] parts = parameters.split("#");
            if (parts.length == 1) {
                itemType = parts[0];
                metadata = null;
            } else if (parts.length == 2) {
                itemType = parts[0];
                assert parts[0].length() > 0;
                metadata = Integer.parseInt(parts[1]);
            } else {
                throw new IllegalArgumentException(String.format("Bad parameter: '%s'", parameters));
            }
            validateMetadata(metadata);
        }

        public String getItemType() {
            return itemType;
        }

        public Integer getMetadata() {
            return metadata;
        }

        public boolean validateItemType() {
            // Sometimes we intentionally send invalid itemType from MineRL -- e.g. "other". In these cases we
            // should just drop the packet. Ideally, we would error on all unexpected cases... (excluding
            // "other" and "none"). For now, there seems to be the default behavior of explicitly ignoring "none".
            Item item = Item.getByNameOrId(getItemType());
            return item != null && item.getRegistryName() != null && !getItemType().equalsIgnoreCase("none");
        }

        @Override
        public void fromBytes(ByteBuf buf) {
            setParameters(ByteBufUtils.readUTF8String(buf));
        }

        @Override
        public void toBytes(ByteBuf buf) {
            ByteBufUtils.writeUTF8String(buf, this.parameters);
        }
    }
}
