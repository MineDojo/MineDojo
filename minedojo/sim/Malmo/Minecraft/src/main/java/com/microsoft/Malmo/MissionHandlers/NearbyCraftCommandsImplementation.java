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

import com.microsoft.Malmo.Schemas.NearbyCraftCommand;
import io.netty.buffer.ByteBuf;

import java.util.ArrayList;
import java.util.List;

import com.google.gson.JsonObject;

import net.minecraft.block.BlockWorkbench;
import net.minecraft.client.Minecraft;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.item.crafting.IRecipe;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.world.BlockEvent;
import net.minecraftforge.fml.common.FMLCommonHandler;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.common.network.ByteBufUtils;
import net.minecraftforge.fml.common.network.simpleimpl.IMessage;
import net.minecraftforge.fml.common.network.simpleimpl.IMessageHandler;
import net.minecraftforge.fml.common.network.simpleimpl.MessageContext;
import net.minecraft.server.MinecraftServer;

import com.microsoft.Malmo.MalmoMod;
import com.microsoft.Malmo.Schemas.MissionInit;
import com.microsoft.Malmo.Schemas.NearbyCraftCommands;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Utils.CraftingHelper;

/**
 * @author Cayden Codel, Carnegie Mellon University
 * <p>
 * Extends the functionality of the SimpleCraftCommands by requiring a crafting table close-by. Only handles crafting, no smelting.
 */
public class NearbyCraftCommandsImplementation extends CommandBase implements IObservationProducer {
    private boolean isOverriding;
    private static ArrayList<BlockPos> craftingTables;

    public static class CraftNearbyMessage implements IMessage {
        String parameters;

        public CraftNearbyMessage(){}

        public CraftNearbyMessage(String parameters) {
            this.parameters = parameters;
        }

        @Override
        public void fromBytes(ByteBuf buf) {
            this.parameters = ByteBufUtils.readUTF8String(buf);
        }

        @Override
        public void toBytes(ByteBuf buf) {
            ByteBufUtils.writeUTF8String(buf, this.parameters);
        }
    }

    public static class CraftingTableMessage implements IMessage {
        BlockPos pos;
        boolean isAdd;

        public CraftingTableMessage(){}

        public CraftingTableMessage(BlockPos pos, boolean isAdd) {
            this.pos = pos;
            this.isAdd = isAdd;
        }

        @Override
        public void fromBytes(ByteBuf buf) {
            this.pos = new BlockPos( buf.readInt(), buf.readInt(), buf.readInt() );
            this.isAdd = buf.readBoolean();
        }

        @Override
        public void toBytes(ByteBuf buf) {
            buf.writeInt(this.pos.getX());
            buf.writeInt(this.pos.getY());
            buf.writeInt(this.pos.getZ());
            buf.writeBoolean(this.isAdd);
        }
    }

    public static class CraftingTableMessageHandler implements IMessageHandler<CraftingTableMessage, IMessage> {
        @Override
        public IMessage onMessage(CraftingTableMessage message, MessageContext ctx) {
            // This ensures there won't be duplicates in the list even if we are adding
            maybeRemoveAtPos(craftingTables, message.pos);
            if (message.isAdd) {
                craftingTables.add(message.pos);
            }
            return null;
        }
    }

    public static void maybeRemoveAtPos(ArrayList<BlockPos> craftingTables, BlockPos pos) {
        for (int i = craftingTables.size() - 1; i >= 0; i--)
            if (craftingTables.get(i).equals(pos))
                craftingTables.remove(i);
    }

    public void sendCraftingTableMessage(BlockPos pos, boolean isAdd) {
        MinecraftServer server = FMLCommonHandler.instance().getMinecraftServerInstance();
        for (Object player : server.getPlayerList().getPlayers()) {
            if (player != null && player instanceof EntityPlayerMP) {
                MalmoMod.network.sendTo(new CraftingTableMessage(pos, isAdd), (EntityPlayerMP) player);
            }
        }
    }

    @SubscribeEvent
    public void onBlockPlace(BlockEvent.PlaceEvent event) {
        if (!event.isCanceled() && event.getPlacedBlock().getBlock() instanceof BlockWorkbench) {
            craftingTables.add(event.getPos());
            if (event.getPlayer() instanceof EntityPlayerMP) {
                // This means this is a server-side message, propagate it to each player.
                sendCraftingTableMessage(event.getPos(), true);
            }
        }
    }

    @SubscribeEvent
    public void onBlockDestroy(BlockEvent.BreakEvent event) {
        if (!event.isCanceled() && event.getState().getBlock() instanceof BlockWorkbench) {
            maybeRemoveAtPos(craftingTables, event.getPos());
            if (event.getPlayer() instanceof EntityPlayerMP) {
                // This means this is a server-side message, propagate it to each player.
                sendCraftingTableMessage(event.getPos(), false);
            }
        }
    }

    public static boolean hasNearbyCraftingTable(EntityPlayer player, ArrayList<BlockPos> craftingTables) {
        Vec3d headPos = new Vec3d(player.posX, player.posY + 1.6, player.posZ);

        // Location checking
        boolean closeTable = false;
        for (BlockPos furnace : craftingTables) {
            Vec3d blockVec = new Vec3d(furnace.getX() + 0.5, furnace.getY() + 0.5, furnace.getZ() + 0.5);

            if (headPos.squareDistanceTo(blockVec) <= 25.0) {
                // Within a reasonable FOV?
                // Lots of trig, let's go
                double fov = Minecraft.getMinecraft().gameSettings.fovSetting;
                double height = Minecraft.getMinecraft().displayHeight;
                double width = Minecraft.getMinecraft().displayWidth;
                Vec3d lookVec = player.getLookVec();
                Vec3d toBlock = blockVec.subtract(headPos);

                // Projection of block onto player look vector - if greater than 0, then in front of us
                double scalarProjection = lookVec.dotProduct(toBlock) / lookVec.lengthVector();
                if (scalarProjection > 0) {
                    Vec3d yUnit = new Vec3d(0, 1.0, 0);
                    Vec3d lookCross = lookVec.crossProduct(yUnit);
                    Vec3d blockProjectedOntoCross = lookCross.scale(lookCross.dotProduct(toBlock) / lookCross.lengthVector());
                    Vec3d blockProjectedOntoPlayerPlane = toBlock.subtract(blockProjectedOntoCross);
                    double xyDot = lookVec.dotProduct(blockProjectedOntoPlayerPlane);
                    double pitchTheta = Math.acos(xyDot / (lookVec.lengthVector() * blockProjectedOntoPlayerPlane.lengthVector()));

                    Vec3d playerY = lookCross.crossProduct(lookVec);
                    Vec3d blockProjectedOntoPlayerY = playerY.scale(playerY.dotProduct(toBlock) / playerY.lengthVector());
                    Vec3d blockProjectedOntoYawPlane = toBlock.subtract(blockProjectedOntoPlayerY);
                    double xzDot = lookVec.dotProduct(blockProjectedOntoYawPlane);
                    double yawTheta = Math.acos(xzDot / (lookVec.lengthVector() * blockProjectedOntoYawPlane.lengthVector()));

                    if (Math.abs(Math.toDegrees(yawTheta)) <= Math.min(1, width / height) * (fov / 2.0) && Math.abs(Math.toDegrees(pitchTheta)) <= Math.min(1, height / width) * (fov / 2.0))
                        closeTable = true;
                }
            }
        }
        return closeTable;
    }

    public static class CraftNearbyMessageHandler implements IMessageHandler<CraftNearbyMessage, IMessage> {
        @Override
        public IMessage onMessage(CraftNearbyMessage message, MessageContext ctx) {
            EntityPlayerMP player = ctx.getServerHandler().playerEntity;
            boolean closeTable = hasNearbyCraftingTable(player, craftingTables);
            if (closeTable) {
                // We are close enough, try crafting recipes
                List<IRecipe> matching_recipes;
                String[] split = message.parameters.split(" ");
                if (split.length > 1)
                    matching_recipes = CraftingHelper.getRecipesForRequestedOutput(message.parameters, true);
                else
                    matching_recipes = CraftingHelper.getRecipesForRequestedOutput(message.parameters, false);

                for (IRecipe recipe : matching_recipes)
                    if (CraftingHelper.attemptCrafting(player, recipe))
                        return null;
            }

            return null;
        }
    }

    @Override
    protected boolean onExecute(String verb, String parameter, MissionInit missionInit) {
        if (verb.equalsIgnoreCase("craftNearby") && !parameter.equalsIgnoreCase("none")) {
            MalmoMod.network.sendToServer(new CraftNearbyMessage(parameter));
            return true;
        }
        return false;
    }

    @Override
    public boolean parseParameters(Object params) {
        if (!(params instanceof NearbyCraftCommands))
            return false;

        craftingTables = new ArrayList<BlockPos>();

        NearbyCraftCommands cParams = (NearbyCraftCommands) params;
        setUpAllowAndDenyLists(cParams.getModifierList());
        return true;
    }

    @Override
    public void install(MissionInit missionInit) {
        CraftingHelper.reset();
        MinecraftForge.EVENT_BUS.register(this);
    }

    @Override
    public void deinstall(MissionInit missionInit) {
        MinecraftForge.EVENT_BUS.unregister(this);
    }

    @Override
    public boolean isOverriding() {
        return this.isOverriding;
    }

    @Override
    public void setOverriding(boolean b) {
        this.isOverriding = b;
    }

    @Override
    public void prepare(MissionInit missionInit)
    {
    }

    @Override
    public void cleanup()
    {
    }

    @Override
    public void writeObservationsToJSON(JsonObject json, MissionInit missionInit)
    {
        json.addProperty("nearby_crafting_table", hasNearbyCraftingTable(Minecraft.getMinecraft().player, craftingTables));
    }
}