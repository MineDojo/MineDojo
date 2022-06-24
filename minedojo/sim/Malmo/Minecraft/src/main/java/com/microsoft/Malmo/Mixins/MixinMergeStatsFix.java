package com.microsoft.Malmo.Mixins;
import net.minecraft.block.Block;
import net.minecraft.item.Item;
import net.minecraft.init.Items;
import net.minecraft.stats.StatBase;
import net.minecraft.stats.StatList;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;

@Mixin(StatList.class)
public abstract class MixinMergeStatsFix {
    /**
     * @author Joost Huizinga
     */
    @Overwrite
    private static void mergeStatBases(StatBase[] statBaseIn, Block block1, Block block2, boolean useItemIds)
    {
        int i;
        int j;
        if (useItemIds) {
            i = Item.getIdFromItem(Item.getItemFromBlock(block1));
            j = Item.getIdFromItem(Item.getItemFromBlock(block2));
            if (i == Item.getIdFromItem(Items.AIR) || j == Item.getIdFromItem(Items.AIR) || i == j) {
                // If any of these conditions is true, the merge won't actually do anything, or it will remove
                // valid statistics.
                return;
            }
        } else {
            i = Block.getIdFromBlock(block1);
            j = Block.getIdFromBlock(block2);
        }
        if (statBaseIn[i] != null && statBaseIn[j] == null)
        {
            statBaseIn[j] = statBaseIn[i];
        }
        else if(statBaseIn[i] == null && statBaseIn[j] != null) {
            statBaseIn[i] = statBaseIn[j];
        }
    }
}
