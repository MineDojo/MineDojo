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

package com.microsoft.Malmo.Utils;

import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.util.*;
import java.io.*;

import com.google.common.base.CaseFormat;
import com.google.gson.*;
import com.microsoft.Malmo.MissionHandlers.RewardForCollectingItemImplementation;
import com.microsoft.Malmo.MissionHandlers.RewardForDiscardingItemImplementation;

import com.microsoft.Malmo.Schemas.RayOffset;
import net.minecraft.block.Block;
import net.minecraft.block.BlockPlanks;
import net.minecraft.block.BlockWall;
import net.minecraft.block.material.EnumPushReaction;
import net.minecraft.block.material.Material;
import net.minecraft.block.properties.IProperty;
import net.minecraft.block.properties.PropertyDirection;
import net.minecraft.block.properties.PropertyEnum;
import net.minecraft.block.state.IBlockState;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.creativetab.CreativeTabs;

import net.minecraft.entity.EntityLiving;
import net.minecraft.entity.item.EntityXPOrb;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.init.Blocks;
import net.minecraft.init.Items;
import net.minecraft.inventory.InventoryCrafting;
import net.minecraft.item.*;
import net.minecraft.item.crafting.*;
import net.minecraft.stats.Achievement;
import net.minecraft.stats.AchievementList;
import net.minecraft.stats.StatBase;
import net.minecraft.stats.StatList;
import net.minecraft.tileentity.TileEntityFurnace;
import net.minecraft.util.NonNullList;
import net.minecraft.util.ResourceLocation;
import net.minecraft.util.math.MathHelper;
import net.minecraftforge.common.MinecraftForge;

import net.minecraftforge.oredict.OreDictionary;
import net.minecraftforge.oredict.ShapedOreRecipe;
import net.minecraftforge.oredict.ShapelessOreRecipe;

public class CraftingHelper {
    private static Map<EntityPlayerMP, Integer> fuelCaches = new HashMap<EntityPlayerMP, Integer>();
    private static final int smeltingCookingTime = new TileEntityFurnace().getCookTime(null); // same for all items, apparently
    /**
     * Reset caches<br>
     * Needed to make sure the player starts with a fresh fuel stash.
     */
    public static void reset() {
        fuelCaches = new HashMap<EntityPlayerMP, Integer>();
    }

    /**
     * Attempt to return the raw ingredients required for this recipe.<br>
     * Ignores all shaping.
     *
     * @param recipe the IRecipe to dissect.
     * @return a list of ItemStacks, amalgamated so that all items of the same type are placed in the same stack.
     */
    public static NonNullList<ItemStack> getIngredients(IRecipe recipe) {
        // IRecipe helpfully has no method for inspecting the raw ingredients, so we need to do different things depending on the subclass.
        NonNullList<ItemStack> ingredients = NonNullList.create();
        if (recipe instanceof ShapelessRecipes) {
            List<?> items = ((ShapelessRecipes) recipe).recipeItems;
            for (Object obj : items) {
                if (obj instanceof ItemStack)
                    ingredients.add((ItemStack) obj);
            }
        } else if (recipe instanceof ShapelessOreRecipe) {
            NonNullList<Object> objs = ((ShapelessOreRecipe) recipe).getInput();
            for (Object o : objs) {
                if (o != null) {
                    if (o instanceof ItemStack)
                        ingredients.add((ItemStack) o);
                    else if (o instanceof List) {
                        List<?> stacks = (List<?>) o;
                        for (Object stack : stacks) {
                            if (stack instanceof ItemStack)
                                ingredients.add((ItemStack) stack);
                        }
                    }
                }
            }
        } else if (recipe instanceof ShapedRecipes) {
            ItemStack[] recipeItems = ((ShapedRecipes) recipe).recipeItems;
            for (ItemStack itemStack : recipeItems) {
                if (itemStack != null)
                    ingredients.add(itemStack);
            }
        } else if (recipe instanceof ShapedOreRecipe) {
            Object[] items = ((ShapedOreRecipe) recipe).getInput();
            for (Object obj : items) {
                if (obj != null) {
                    if (obj instanceof ItemStack)
                        ingredients.add((ItemStack) obj);
                    else if (obj instanceof List) {
                        List<?> stacks = (List<?>) obj;
                        for (Object stack : stacks) {
                            if (stack instanceof ItemStack)
                                ingredients.add((ItemStack) stack);
                        }
                    }
                }
            }
        } else {
            // TODO Implement remaining recipe types after incorporating item metadata (e.g. potions for tipped arrows)
            return ingredients;
        }
        return consolidateItemStacks(ingredients);
    }

    /**
     * Take a list of ItemStacks and amalgamate where possible.<br>
     *
     * @param inputStacks a list of ItemStacks
     * @return a list of ItemStacks, where all items of the same type are grouped into one stack.
     */
    public static NonNullList<ItemStack> consolidateItemStacks(NonNullList<ItemStack> inputStacks) {
        // Horrible n^2 method - we should do something nicer if this ever becomes a bottleneck.
        NonNullList<ItemStack> outputStacks = NonNullList.create();
        for (ItemStack sourceIS : inputStacks) {
            boolean bFound = false;
            for (ItemStack destIS : outputStacks) {
                if (destIS != null && sourceIS != null && itemStackIngredientsMatch(destIS, sourceIS)) {
                    bFound = true;
                    destIS.setCount(destIS.getCount() + sourceIS.getCount());
                }
            }
            if (!bFound) {
                assert sourceIS != null;
                outputStacks.add(sourceIS.copy());
            }
        }
        return outputStacks;
    }

    /**
     * Inspect a player's inventory to see whether they have enough items to form the supplied list of ItemStacks.<br>
     * The ingredients list MUST be amalgamated such that no two ItemStacks contain the same type of item.
     *
     * @param player
     * @param ingredients an amalgamated list of ingredients
     * @return true if the player's inventory contains sufficient quantities of all the required items.
     */
    public static boolean playerHasIngredients(EntityPlayerMP player, List<ItemStack> ingredients) {
        NonNullList<ItemStack> main = player.inventory.mainInventory;
        NonNullList<ItemStack> arm = player.inventory.armorInventory;

        for (ItemStack isIngredient : ingredients) {
            int target = isIngredient.getCount();
            for (int i = 0; i < main.size() + arm.size() && target > 0; i++) {
                ItemStack isPlayer = (i >= main.size()) ? arm.get(i - main.size()) : main.get(i);
                if (isPlayer != null && isIngredient != null && itemStackIngredientsMatch(isPlayer, isIngredient))
                    target -= isPlayer.getCount();
            }
            if (target > 0)
                return false;   // Don't have enough of this.
        }
        return true;
    }

    /**
     * Inspect a player's inventory to see whether they have enough items to form the supplied list of ItemStacks.<br>
     * The ingredients list MUST be amalgamated such that no two ItemStacks contain the same type of item.
     *
     * @param player
     * @param ingredients an amalgamated list of ingredients
     * @return true if the player's inventory contains sufficient quantities of all the required items.
     */
    public static boolean playerHasIngredients(EntityPlayerSP player, List<ItemStack> ingredients) {
        NonNullList<ItemStack> main = player.inventory.mainInventory;
        NonNullList<ItemStack> arm = player.inventory.armorInventory;

        for (ItemStack isIngredient : ingredients) {
            int target = isIngredient.getCount();
            for (int i = 0; i < main.size() + arm.size() && target > 0; i++) {
                ItemStack isPlayer = (i >= main.size()) ? arm.get(i - main.size()) : main.get(i);
                if (isPlayer != null && isIngredient != null && itemStackIngredientsMatch(isPlayer, isIngredient))
                    target -= isPlayer.getCount();
            }
            if (target > 0)
                return false;   // Don't have enough of this.
        }
        return true;
    }

    /**
     * Compare two ItemStacks and see if their items match - take wildcards into account, don't take stacksize into account.
     *
     * @param A ItemStack A
     * @param B ItemStack B
     * @return true if the stacks contain matching items.
     */
    private static boolean itemStackIngredientsMatch(ItemStack A, ItemStack B) {
        if (A == null && B == null)
            return true;
        if (A == null || B == null)
            return false;
        if (A.getMetadata() == OreDictionary.WILDCARD_VALUE || B.getMetadata() == OreDictionary.WILDCARD_VALUE)
            return A.getItem() == B.getItem();
        return ItemStack.areItemsEqual(A, B);
    }

    /**
     * Go through player's inventory and see how much fuel they have.
     *
     * @param player
     * @return the amount of fuel available in ticks
     */
    public static int totalBurnTimeInInventory(EntityPlayerMP player) {
        Integer fromCache = fuelCaches.get(player);
        int total = (fromCache != null) ? fromCache : 0;
        for (int i = 0; i < player.inventory.mainInventory.size(); i++) {
            ItemStack is = player.inventory.mainInventory.get(i);
            total += is.getCount() * TileEntityFurnace.getItemBurnTime(is);
        }
        return total;
    }

    /**
     * Consume fuel from the player's inventory.<br>
     * Take it first from their cache, if present, and then from their inventory, starting
     * at the first slot and working upwards.
     *
     * @param player
     * @param burnAmount amount of fuel to burn, in ticks.
     */
    public static void burnInventory(EntityPlayerMP player, int burnAmount, ItemStack input) {
        if (!fuelCaches.containsKey(player))
            fuelCaches.put(player, -burnAmount);
        else
            fuelCaches.put(player, fuelCaches.get(player) - burnAmount);
        int index = 0;
        while (fuelCaches.get(player) < 0 && index < player.inventory.mainInventory.size()) {
            ItemStack is = player.inventory.mainInventory.get(index);
            if (is != null) {
                int burnTime = TileEntityFurnace.getItemBurnTime(is);
                if (burnTime != 0) {
                    // Consume item:
                    if (is.getCount() > 1)
                        is.setCount(is.getCount() - 1);
                    else {
                        // If this is a bucket of lava, we need to consume the lava but leave the bucket.
                        if (is.getItem() == Items.LAVA_BUCKET) {
                            // And if we're cooking wet sponge, we need to leave the bucket filled with water.
                            if (input.getItem() == Item.getItemFromBlock(Blocks.SPONGE) && input.getMetadata() == 1)
                                player.inventory.mainInventory.set(index, new ItemStack(Items.WATER_BUCKET));
                            else
                                player.inventory.mainInventory.set(index, new ItemStack(Items.BUCKET));
                        } else
                            player.inventory.mainInventory.get(index).setCount(0);
                        index++;
                    }
                    fuelCaches.put(player, fuelCaches.get(player) + burnTime);
                } else
                    index++;
            } else
                index++;
        }
    }

    /**
     * Manually attempt to remove ingredients from the player's inventory.<br>
     *
     * @param player
     * @param ingredients
     */
    public static void removeIngredientsFromPlayer(EntityPlayerMP player, List<ItemStack> ingredients) {
        NonNullList<ItemStack> main = player.inventory.mainInventory;
        NonNullList<ItemStack> arm = player.inventory.armorInventory;

        for (ItemStack isIngredient : ingredients) {
            int target = isIngredient.getCount();
            for (int i = 0; i < main.size() + arm.size() && target > 0; i++) {
                ItemStack isPlayer = (i >= main.size()) ? arm.get(i - main.size()) : main.get(i);
                if (itemStackIngredientsMatch(isPlayer, isIngredient)) {
                    if (target >= isPlayer.getCount()) {
                        // Consume this stack:
                        target -= isPlayer.getCount();
                        if (i >= main.size())
                            arm.get(i - main.size()).setCount(0);
                        else
                            main.get(i).setCount(0);
                    } else {
                        isPlayer.setCount(isPlayer.getCount() - target);
                        target = 0;
                    }
                }
            }
            ItemStack resultForReward = isIngredient.copy();
            RewardForDiscardingItemImplementation.LoseItemEvent event = new RewardForDiscardingItemImplementation.LoseItemEvent(
                    player, resultForReward);
            MinecraftForge.EVENT_BUS.post(event);
        }
    }

    /**
     * Attempt to find all recipes that result in an item of the requested output.
     *
     * @param output the desired item, eg from Types.xsd - "diamond_pickaxe" etc - or as a Minecraft name - eg "tile.woolCarpet.blue"
     * @param variant if variants should be obeyed in constructing the recipes, i.e. if false, variant blind
     * @return a list of IRecipe objects that result in this item.
     */
    public static List<IRecipe> getRecipesForRequestedOutput(String output, boolean variant) {
        List<IRecipe> matchingRecipes = new ArrayList<IRecipe>();
        ItemStack target = MinecraftTypeHelper.getItemStackFromParameterString(output);
        List<?> recipes = CraftingManager.getInstance().getRecipeList();
        for (Object obj : recipes) {
            if (obj == null)
                continue;
            if (obj instanceof IRecipe) {
                ItemStack is = ((IRecipe) obj).getRecipeOutput();
                if (target == null)
                    continue;
                if (variant && ItemStack.areItemsEqual(is, target))
                    matchingRecipes.add((IRecipe) obj);
                else if (!variant && is.getItem() == target.getItem())
                    matchingRecipes.add((IRecipe) obj);
            }
        }
        return matchingRecipes;
    }

    /**
     * Attempt to find all recipes that result in an item of the requested output.
     *
     * @param output the desired item, eg from Types.xsd - "diamond_pickaxe" etc - or as a Minecraft name - eg "tile.woolCarpet.blue"
     * @param variant if variants should be obeyed in constructing the recipes, i.e. if false, variant blind
     * @return a list of IRecipe objects that result in this item.
     */
    public static List<IRecipe> getRecipesForRequestedOutput(ItemStack output, boolean variant) {
        List<IRecipe> matchingRecipes = new ArrayList<IRecipe>();
        List<?> recipes = CraftingManager.getInstance().getRecipeList();
        for (Object obj : recipes) {
            if (obj == null)
                continue;
            if (obj instanceof IRecipe) {
                ItemStack is = ((IRecipe) obj).getRecipeOutput();
                if (output == null)
                    continue;
                if (variant && ItemStack.areItemsEqual(is, output))
                    matchingRecipes.add((IRecipe) obj);
                else if (!variant && is.getItem() == output.getItem())
                    matchingRecipes.add((IRecipe) obj);
            }
        }
        return matchingRecipes;
    }

    /**
     * Attempt to find a smelting recipe that results in the requested output.
     *
     * @param output The output of the furnace burn
     * @return an ItemStack representing the required input.
     */
    public static ItemStack getSmeltingRecipeForRequestedOutput(String output, EntityPlayerMP player) {
        ItemStack target = MinecraftTypeHelper.getItemStackFromParameterString(output);
        if (target == null)
            return null;
        for (Map.Entry<ItemStack, ItemStack> e : FurnaceRecipes.instance().getSmeltingList().entrySet()) {
            if (itemStackIngredientsMatch(target, e.getValue())
                    && playerHasIngredients(player, Collections.singletonList(e.getKey()))
                    && totalBurnTimeInInventory(player) >= smeltingCookingTime
                    ) {
                return e.getKey();
            }
        }
        return null;
    }

    /**
     * This code is copied from SlotCrafting.onCrafting
     * TODO - convert this into a mixin to avoid duplicating code
     * @param player - player crafting the items
     * @param stack - item and quantity that was crafted
     * @param craftMatrix - the InventoryCrafting representing the item recipe
     */
    protected static void onCrafting(EntityPlayer player, ItemStack stack, InventoryCrafting craftMatrix)
    {
        // Unclear why you would get achievements without crafting a non-zero amount of an item but this is behavior
        // directly from MC
        if (stack.getCount() > 0)
        {
            stack.onCrafting(player.world, player, stack.getCount());
            net.minecraftforge.fml.common.FMLCommonHandler.instance().firePlayerCraftingEvent(player, stack, craftMatrix);
        }

        if (stack.getItem() == Item.getItemFromBlock(Blocks.CRAFTING_TABLE))
        {
            player.addStat(AchievementList.BUILD_WORK_BENCH);
        }

        if (stack.getItem() instanceof ItemPickaxe)
        {
            player.addStat(AchievementList.BUILD_PICKAXE);
        }

        if (stack.getItem() == Item.getItemFromBlock(Blocks.FURNACE))
        {
            player.addStat(AchievementList.BUILD_FURNACE);
        }

        if (stack.getItem() instanceof ItemHoe)
        {
            player.addStat(AchievementList.BUILD_HOE);
        }

        if (stack.getItem() == Items.BREAD)
        {
            player.addStat(AchievementList.MAKE_BREAD);
        }

        if (stack.getItem() == Items.CAKE)
        {
            player.addStat(AchievementList.BAKE_CAKE);
        }

        if (stack.getItem() instanceof ItemPickaxe && ((ItemPickaxe)stack.getItem()).getToolMaterial() != Item.ToolMaterial.WOOD)
        {
            player.addStat(AchievementList.BUILD_BETTER_PICKAXE);
        }

        if (stack.getItem() instanceof ItemSword)
        {
            player.addStat(AchievementList.BUILD_SWORD);
        }

        if (stack.getItem() == Item.getItemFromBlock(Blocks.ENCHANTING_TABLE))
        {
            player.addStat(AchievementList.ENCHANTMENTS);
        }

        if (stack.getItem() == Item.getItemFromBlock(Blocks.BOOKSHELF))
        {
            player.addStat(AchievementList.BOOKCASE);
        }
    }

    /**
     * Attempt to craft the given recipe.<br>
     * This pays no attention to tedious things like using the right crafting table
     * / brewing stand etc, or getting the right shape.<br>
     * It simply takes the raw ingredients out of the player's inventory, and
     * inserts the output of the recipe, if possible.
     *
     * @param player the SERVER SIDE player that will do the crafting.
     * @param recipe the IRecipe we wish to craft.
     * @return true if the recipe had an output, and the player had the required
     *         ingred:xients to create it; false otherwise.
     */
    public static boolean attemptCrafting(EntityPlayerMP player, IRecipe recipe) {
        if (player == null || recipe == null)
            return false;

        ItemStack is = recipe.getRecipeOutput();

        List<ItemStack> ingredients = getIngredients(recipe);
        if (playerHasIngredients(player, ingredients)) {
            // We have the ingredients we need, so directly manipulate the inventory.
            // First, remove the ingredients:
            removeIngredientsFromPlayer(player, ingredients);
            // Now add the output of the recipe:
            ItemStack resultForInventory = is.copy();
            ItemStack resultForReward = is.copy();
            player.inventory.addItemStackToInventory(resultForInventory);
            RewardForCollectingItemImplementation.GainItemEvent event = new RewardForCollectingItemImplementation.GainItemEvent(
                    player, resultForReward);
            event.setCause(1);
            MinecraftForge.EVENT_BUS.post(event);

            // Now trigger a craft event
            List<IRecipe> recipes = getRecipesForRequestedOutput(resultForReward, true);
            for (IRecipe iRecipe : recipes) {
                if (iRecipe instanceof ShapedRecipes) {
                    ShapedRecipes shapedRecipe = (ShapedRecipes) iRecipe;
                    InventoryCrafting craftMatrix;
                    if (shapedRecipe.recipeItems.length <= 4)
                        craftMatrix = new InventoryCrafting(player.inventoryContainer, 2, 2);
                    else
                        craftMatrix = new InventoryCrafting(player.inventoryContainer, 3, 3);
                    for (int i = 0; i < shapedRecipe.recipeItems.length; i++)
                        craftMatrix.setInventorySlotContents(i, shapedRecipe.recipeItems[i]);

                    onCrafting(player, resultForReward, craftMatrix);
                    break;
                } else if (iRecipe instanceof ShapelessRecipes) {
                    ShapelessRecipes shapelessRecipe = (ShapelessRecipes) iRecipe;
                    InventoryCrafting craftMatrix;
                    if (shapelessRecipe.recipeItems.size() <= 4) {
                        craftMatrix = new InventoryCrafting(player.inventoryContainer, 2, 2);
                        for (int i = 0; i < shapelessRecipe.recipeItems.size(); i++)
                            craftMatrix.setInventorySlotContents(i, shapelessRecipe.recipeItems.get(i));
                    } else {
                        craftMatrix = new InventoryCrafting(player.inventoryContainer, 3, 3);
                        for (int i = 0; i < shapelessRecipe.recipeItems.size(); i++)
                            craftMatrix.setInventorySlotContents(i, shapelessRecipe.recipeItems.get(i));
                    }
                    onCrafting(player, resultForReward, craftMatrix);
                    break;
                } else if (iRecipe instanceof ShapedOreRecipe) {
                    ShapedOreRecipe oreRecipe = (ShapedOreRecipe) iRecipe;
                    Object[] input = oreRecipe.getInput();
                    InventoryCrafting craftMatrix = new InventoryCrafting(player.inventoryContainer, 3, 3);
                    for (int i = 0; i < input.length; i++) {
                        if (input[i] instanceof ItemStack)
                            craftMatrix.setInventorySlotContents(i, (ItemStack) input[i]);
                        else if (input[i] instanceof NonNullList)
                            if (((NonNullList) input[i]).size() != 0)
                                craftMatrix.setInventorySlotContents(i, (ItemStack) ((NonNullList) input[i]).get(0));
                    }
                    onCrafting(player, resultForReward, craftMatrix);
                }
            }
            return true;
        }
        return false;
    }

    /**
     * TODO Copied from SlotFurncaeOutput.onCrafting - change to mixin to remove redundant code
     * @param stack - item stack that was crafted
     */
    protected static void onSmelting(EntityPlayer player, ItemStack stack)
    {
        stack.onCrafting(player.world, player, stack.getCount());

        if (!player.world.isRemote)
        {
            int i = stack.getCount();
            float f = FurnaceRecipes.instance().getSmeltingExperience(stack);

            if (f == 0.0F)
            {
                i = 0;
            }
            else if (f < 1.0F)
            {
                int j = MathHelper.floor((float)i * f);

                if (j < MathHelper.ceil((float)i * f) && Math.random() < (double)((float)i * f - (float)j))
                {
                    ++j;
                }

                i = j;
            }

            while (i > 0)
            {
                int k = EntityXPOrb.getXPSplit(i);
                i -= k;
                player.world.spawnEntity(new EntityXPOrb(player.world, player.posX, player.posY + 0.5D, player.posZ + 0.5D, k));
            }
        }

        net.minecraftforge.fml.common.FMLCommonHandler.instance().firePlayerSmeltedEvent(player, stack);

        if (stack.getItem() == Items.IRON_INGOT)
        {
            player.addStat(AchievementList.ACQUIRE_IRON);
        }

        if (stack.getItem() == Items.COOKED_FISH)
        {
            player.addStat(AchievementList.COOK_FISH);
        }
    }

    /**
     * Attempt to smelt the given item.<br>
     * This returns instantly, callously disregarding such frivolous niceties as cooking times or the presence of a furnace.<br>
     * It will, however, consume fuel from the player's inventory.
     *
     * @param player
     * @param input  the raw ingredients we want to cook.
     * @return true if cooking was successful.
     */
    public static boolean attemptSmelting(EntityPlayerMP player, ItemStack input) {
        if (player == null || input == null)
            return false;
        List<ItemStack> ingredients = new ArrayList<ItemStack>();
        ingredients.add(input);
        ItemStack isOutput = FurnaceRecipes.instance().getSmeltingList().get(input);
        if (isOutput == null)
            return false;
        if (playerHasIngredients(player, ingredients) && totalBurnTimeInInventory(player) >= smeltingCookingTime) {
            removeIngredientsFromPlayer(player, ingredients);
            burnInventory(player, smeltingCookingTime, input);

            ItemStack resultForInventory = isOutput.copy();
            ItemStack resultForReward = isOutput.copy();
            player.inventory.addItemStackToInventory(resultForInventory);
            RewardForCollectingItemImplementation.GainItemEvent event = new RewardForCollectingItemImplementation.GainItemEvent(
                    player, resultForReward);
            event.setCause(2);
            MinecraftForge.EVENT_BUS.post(event);

            // Trigger the furnace output removed item events
            onSmelting(player, isOutput);
            return true;
        }
        return false;
    }

    private static JsonObject listIngredients(NonNullList<ItemStack> ingredients){
        JsonObject jsonObject = new JsonObject();
        for (ItemStack ingredient: ingredients){
            if (!ingredient.isEmpty() && Item.REGISTRY.getNameForObject(ingredient.getItem()) != null)
                jsonObject.addProperty(Item.REGISTRY.getNameForObject(ingredient.getItem()).toString().replace("minecraft:", ""), ingredient.getCount());
        }
        return jsonObject;
    }

    /**
     * Little utility method for dumping out a json array of all the Minecraft items,  plus as many useful
     * attributes as we can find for them. This is primarily used by decision_tree_test.py but might be useful for
     * real-world applications too.
     */
    public static JsonArray generateItemJson(){
        JsonArray items = new JsonArray();
        for (ResourceLocation i : Item.REGISTRY.getKeys()) {
            Item item = Item.REGISTRY.getObject(i);
            if (item != null && Item.REGISTRY.getNameForObject(item) != null) {
                JsonObject json = new JsonObject();
                json.addProperty("type", Item.REGISTRY.getNameForObject(item).toString().replace("minecraft:", ""));
                json.addProperty("damageable", item.isDamageable());
                json.addProperty("rendersIn3D", item.isFull3D());
                json.addProperty("repairable", item.isRepairable());
                CreativeTabs tab = item.getCreativeTab();
                json.addProperty("tab", ((tab != null) ? item.getCreativeTab().getTabLabel() : "none"));
                ItemStack is = item.getDefaultInstance();
                json.addProperty("stackable", is.isStackable());
                json.addProperty("stackSize", is.getMaxStackSize());
                json.addProperty("useAction", is.getItemUseAction().toString());
                json.addProperty("enchantable", is.isItemEnchantable());
                json.addProperty("rarity", is.getRarity().toString());
                json.addProperty("hasSubtypes", item.getHasSubtypes());
                json.addProperty("maxDamage", is.getMaxDamage());
                json.addProperty("maxUseDuration", is.getMaxItemUseDuration());
                json.addProperty("block", item instanceof ItemBlock);
                json.addProperty("hasContainerItem", item.hasContainerItem());
                json.addProperty("bestEquipmentSlot", EntityLiving.getSlotForItemStack(is).getName());
                if (item instanceof ItemBlock) {
                    ItemBlock ib = (ItemBlock) item;
                    Block b = ib.getBlock();
                    IBlockState bs = b.getDefaultState();
                    json.addProperty("slipperiness", b.slipperiness);
                    json.addProperty("hardness", bs.getBlockHardness(null, null));
                    json.addProperty("causesSuffocation", bs.causesSuffocation());
                    json.addProperty("canProvidePower", bs.canProvidePower());
                    json.addProperty("translucent", bs.isTranslucent());
                    Material mat = bs.getMaterial();
                    json.addProperty("canBurn", mat.getCanBurn());
                    json.addProperty("isLiquid", mat.isLiquid());
                    json.addProperty("isSolid", mat.isSolid());
                    json.addProperty("blocksMovement", mat.blocksMovement());
                    json.addProperty("needsNoTool", mat.isToolNotRequired());
                    json.addProperty("isReplaceable", mat.isReplaceable());
                    json.addProperty("pistonPushable", mat.getMobilityFlag() == EnumPushReaction.NORMAL);
                    json.addProperty("woodenMaterial", mat == Material.WOOD);
                    json.addProperty("ironMaterial", mat == Material.IRON);
                    json.addProperty("glassyMaterial", mat == Material.GLASS);
                    json.addProperty("clothMaterial", mat == Material.CLOTH);

                    boolean hasDirection = false;
                    boolean hasColour = false;
                    boolean hasVariant = false;
                    boolean hasType = false;
                    boolean hasHalf = false;
                    for (IProperty prop : bs.getProperties().keySet()) {
                        System.out.println(Item.REGISTRY.getNameForObject(item).toString() + " -- " + prop);
                        if (prop instanceof PropertyDirection)
                            hasDirection = true;
                        if (prop instanceof PropertyEnum && prop.getName().equals("color"))
                            hasColour = true;
                        if (prop instanceof PropertyEnum && prop.getName().equals("half"))
                            hasHalf = true;
                        if (prop instanceof PropertyEnum && (prop.getName().equals("variant") || prop.getName().equals("type"))) {
                            if (prop.getName().equals("variant")) {
                                hasVariant = true;
                            } else {
                                hasType = true;
                            }
                            // we record both variants and types as "variant"
                            JsonArray arr = new JsonArray();
                            for (Object variant_type : ((PropertyEnum)prop).getAllowedValues()) {
                                arr.add(new JsonPrimitive(variant_type.toString()));
                            }
                            json.add("variant", arr);
                        }
                    }
                    json.addProperty("hasDirection", hasDirection);
                    json.addProperty("hasColour", hasColour);
                    json.addProperty("hasVariant", hasVariant);
                    json.addProperty("hasType", hasType);
                    json.addProperty("hasHalf", hasHalf);
                }
                items.add(json);
            }
        }
        return items;
    }

    /**
     * Little utility method for generating a json array of all of the Minecraft blocks
     */
    public static JsonArray generateBlockJson(){
        JsonArray blocks = new JsonArray();
        for (ResourceLocation i : Block.REGISTRY.getKeys()) {
            Block block = Block.REGISTRY.getObject(i);
            JsonObject json = new JsonObject();
            json.addProperty("name", Block.REGISTRY.getNameForObject(block).toString().replace("minecraft:", ""));
            json.addProperty("particleGravity", block.blockParticleGravity);
            json.addProperty("slipperiness", block.slipperiness);
            json.addProperty("spawnInBlock", block.canSpawnInBlock());
            json.addProperty("isCollidable", block.isCollidable());
            try{
                json.addProperty("quantityDropped", block.quantityDropped(null));
            } catch (NullPointerException ignored){}
            blocks.add(json);
        }
        return blocks;
    }

    /**
     * Little utility method for generating a json array of all of the Minecraft achievements
     */
    public static JsonArray generateAchievements(){
        JsonArray achievements = new JsonArray();
        for (Achievement achievement : AchievementList.ACHIEVEMENTS) {
            JsonObject json = new JsonObject();
            json.addProperty("statID", achievement.statId);
            if (achievement.parentAchievement != null && achievement.parentAchievement.statId != null)
                json.addProperty("parentStatID", achievement.parentAchievement.statId);
            json.addProperty("isIndependent", achievement.isIndependent);
            json.addProperty("displayColumn", achievement.displayColumn);
            json.addProperty("displayRow", achievement.displayRow);
            json.addProperty("isSpecial", achievement.getSpecial());
            json.addProperty("description", achievement.getDescription());

            achievements.add(json);
        }
        return achievements;
    }


    /**
     * Little utility method for generating a json array of all of the Minecraft base stats
     */
    public static JsonArray generateStats(){
        JsonArray stats = new JsonArray();
        for (StatBase stat : StatList.ALL_STATS) {
            JsonObject json = new JsonObject();
            json.addProperty("statID", stat.statId);
            JsonArray tokens = new JsonArray();
            for (String token : stat.statId.split("\\.")){
                // BAH map drop stat to items_dropped to prevent hash collision in dict keys
                // MUST change this in JSONWorldDataHelper.java as well!!!! (search above comment)
                if (token.equals(stat.statId.split("\\.")[stat.statId.split("\\.").length - 1]))
                    if (token.equals("drop"))
                        token = "items_dropped";
                tokens.add(new JsonPrimitive(CaseFormat.UPPER_CAMEL.to(CaseFormat.LOWER_UNDERSCORE, token)));
            }
            json.add("minerl_keys", tokens);
            json.addProperty("isIndependent", stat.isIndependent);
            json.addProperty("isAchievement",stat.isAchievement());
            stats.add(json);
        }
        return stats;
    }


    /**
     * Little utility method for generating a json array of all of the Minecraft crafting recipes
     */
    public static JsonArray generateCraftingRecipeJson(){
        JsonArray craftingRecipes = new JsonArray();
        for (IRecipe recipe : CraftingManager.getInstance().getRecipeList()) {
            if (recipe == null || Item.REGISTRY.getNameForObject(recipe.getRecipeOutput().getItem()) == null)
                continue;
            JsonObject jsonObject = new JsonObject();
            jsonObject.addProperty("outputItemName", Item.REGISTRY.getNameForObject(recipe.getRecipeOutput().getItem()).toString().replace("minecraft:", ""));
            jsonObject.addProperty("outputCount", recipe.getRecipeOutput().getCount());
            jsonObject.addProperty("recipeSize", recipe.getRecipeSize());
            jsonObject.addProperty("type", recipe.getClass().getSimpleName());
            jsonObject.add( "ingredients", listIngredients(getIngredients(recipe)));
            craftingRecipes.add(jsonObject);
        }
        return craftingRecipes;
    }

    /**
     * Little utility method for generating a json array of all of the Minecraft smelting recipes
     */
    public static JsonArray generateSmeltingRecipeJson(){
        JsonArray smeltingRecipes = new JsonArray();
        for (ItemStack isInput : FurnaceRecipes.instance().getSmeltingList().keySet()) {
            ItemStack isOutput = FurnaceRecipes.instance().getSmeltingList().get(isInput);
            if (Item.REGISTRY.getNameForObject(isOutput.getItem()) == null)
                continue;
            JsonObject jsonObject = new JsonObject();
            jsonObject.addProperty("outputItemName", Item.REGISTRY.getNameForObject(isOutput.getItem()).toString().replace("minecraft:", ""));
            jsonObject.addProperty("out", isOutput.getCount());
            jsonObject.add("ingredients", listIngredients(NonNullList.withSize(1, isInput)));
            smeltingRecipes.add(jsonObject);
        }
        return smeltingRecipes;
    }

    /**
     * Little utility method for dumping out a list of all the Minecraft items, plus as many useful attributes as
     * we can find for them. This is primarily used by decision_tree_test.py but might be useful for real-world applications too.
     *
     * @param filename location to save the dumped list.
     * @throws IOException
     */
    public static void dumpItemProperties(String filename) throws IOException {
        FileOutputStream fos = new FileOutputStream("..//..//build//install//Python_Examples//item_database.json");
        OutputStreamWriter osw = new OutputStreamWriter(fos, "utf-8");
        BufferedWriter writer = new BufferedWriter(osw);
        JsonArray itemTypes = generateItemJson();
        writer.write(itemTypes.toString());
        writer.close();
    }

    /**
     * Utility method to auto-generate item, block, and recipe lists as individual json arrays
     *
     * @param filename location to save the dumped json file.
     */
    public static void dumpMinecraftObjectRules(String filename) {
        JsonObject allRecipes = new JsonObject();
        allRecipes.addProperty("docstring", "THIS IS AN AUTO GENERATED FILE! This file was generated by " +
                "com.microsoft.Malmo.Utils.CraftingHelper.dumpMinecraftObjectRules(). Generate this file by " +
                "launching Malmo and pressing the 'u' key (see MalmoModClient.java) or by adding the following to " +
                "MixinMinecraftServerRun.java: CraftingHelper.dumpMinecraftObjectRules(\"/full/path/mc_constants.json\");");
        allRecipes.add("craftingRecipes", generateCraftingRecipeJson());
        allRecipes.add("smeltingRecipes", generateSmeltingRecipeJson());
        allRecipes.add("items", generateItemJson());
        allRecipes.add("blocks", generateBlockJson());
        allRecipes.add("achievements", generateAchievements());
        allRecipes.add("stats", generateStats());
        try {
            Writer writer = new FileWriter(filename);
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            gson.toJson(allRecipes, writer);
            System.out.println("Wrote json to " + System.getProperty("user.dir") + filename);
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
