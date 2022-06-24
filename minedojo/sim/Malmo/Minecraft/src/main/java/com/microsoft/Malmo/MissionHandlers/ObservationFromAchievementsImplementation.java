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

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Schemas.*;
import com.microsoft.Malmo.Utils.MinecraftTypeHelper;
import net.minecraft.block.properties.IProperty;
import net.minecraft.block.state.IBlockState;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.entity.Entity;
import net.minecraft.entity.item.EntityItem;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NBTTagCompound;
import net.minecraft.network.play.client.CPacketClientStatus;
import net.minecraft.stats.Achievement;
import net.minecraft.stats.AchievementList;
import net.minecraft.tileentity.TileEntity;
import net.minecraft.util.math.AxisAlignedBB;
import net.minecraft.util.math.RayTraceResult;
import net.minecraft.util.math.Vec3d;

import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

public class ObservationFromAchievementsImplementation extends HandlerBase implements IObservationProducer
{
    /**
     * Here we simply write out a boolean for each achievement based on the unique statID of that achievement
     * TODO 'special' achievements are more difficult to achieve and could be identified here
     * @param json the JSON object into which to add our observations
     * @param missionInit the MissionInit object for the currently running mission, which may contain parameters for the observation requirements.
     */
    @Override
    public void writeObservationsToJSON(JsonObject json, MissionInit missionInit)
    {
        JsonObject achievements = new JsonObject();
        Minecraft mc = Minecraft.getMinecraft();
        EntityPlayerSP player = mc.player;

        for (Achievement achievement : AchievementList.ACHIEVEMENTS) {
            achievements.addProperty(achievement.statId, player.getStatFileWriter().hasAchievementUnlocked(achievement));
        }

        json.add("achievements", achievements);
    }

    /**
     * Attempt to give the agent the open-inventory achievement by default since it is bound to gui interactions some of
     * which may be bypassed by Malmo
     * @param missionInit not used
     */
    @Override
    public void prepare(MissionInit missionInit)
    {
        if ( Minecraft.getMinecraft().getConnection() != null)
            Minecraft.getMinecraft().getConnection().sendPacket(
                    new CPacketClientStatus(CPacketClientStatus.State.OPEN_INVENTORY_ACHIEVEMENT)
            );
        else
            throw new NullPointerException("Minecraft returned null net handler connection!");
        Minecraft.getMinecraft().player.addStat(AchievementList.OPEN_INVENTORY);
    }

    @Override
    public void cleanup()
    {
    }

}
