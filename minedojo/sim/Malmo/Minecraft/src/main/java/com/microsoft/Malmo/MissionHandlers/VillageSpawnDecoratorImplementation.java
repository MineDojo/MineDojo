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

import com.microsoft.Malmo.MissionHandlerInterfaces.IWorldDecorator;
import com.microsoft.Malmo.Schemas.AgentSection;
import com.microsoft.Malmo.Schemas.MissionInit;
import com.microsoft.Malmo.Schemas.PosAndDirection;
import com.microsoft.Malmo.Schemas.VillageSpawnDecorator;
import com.microsoft.Malmo.Utils.PositionHelper;
import com.microsoft.Malmo.Utils.SeedHelper;

import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Spawns the player in a village.
 * @author Neel Alex
 */
public class VillageSpawnDecoratorImplementation extends HandlerBase implements IWorldDecorator
{
    // ALL OF THIS IS BLATANTLY COPIED FROM RandomizedStartDecoratorImplementation
    // TRUST NOTHING AND NO ONE.
    // Random number generators for path generation / block choosing:
    private Random rand = SeedHelper.getRandom("agentStart");;

    private VillageSpawnDecorator params = null;


    @Override
    public boolean parseParameters(Object params)
    {
        if (params == null || !(params instanceof VillageSpawnDecorator))
            return false;
        this.params = (VillageSpawnDecorator)params;
        return true;
    }

    private void teleportAgents(MissionInit missionInit, World world)
    {
        // Force all players to being at a random starting position
        for (AgentSection as : missionInit.getMission().getAgentSection())
        {
            BlockPos blockPos = world.findNearestStructure("Village", world.getSpawnPoint(), false);
            System.out.println("====0 blockPos (before getTopTeleportable)" + blockPos.toString());

            // `PositionHelper.getTopTeleportableBlock(world, blockPos);` has a more reassuring sounding name, but
            // these two "getTop" helper functions seem to work about the same in terms of chance of spawning the
            // player inside a wall, which leads to "suffocation" death within the first 5 frames.
            blockPos = PositionHelper.getTopSolidOrLiquidBlock(world, blockPos);
            System.out.println("====1 blockPos (after getTop..Block)" + blockPos.toString());

            System.out.println("Selected start:" + blockPos.toString());
            PosAndDirection xmlPos = new PosAndDirection();
            xmlPos.setX(BigDecimal.valueOf(blockPos.getX() + 0.5));
            xmlPos.setY(BigDecimal.valueOf(blockPos.getY() + 2));
            xmlPos.setZ(BigDecimal.valueOf(blockPos.getZ() + 0.5));

            System.out.println(String.format("====2 xmlPos (%f, %f, %f)%n",
                    xmlPos.getX().floatValue(), xmlPos.getY().floatValue(), xmlPos.getZ().floatValue()));

            as.getAgentStart().setPlacement(xmlPos);
        }
    }

    @Override
    public void buildOnWorld(MissionInit missionInit, World world)
    {
        teleportAgents(missionInit, world);
    }
    
    @Override
    public void update(World world) {}

    @Override
    public boolean getExtraAgentHandlersAndData(List<Object> handlers, Map<String, String> data) { return false; }

    @Override
    public void prepare(MissionInit missionInit)
    {
    }

    @Override
    public void cleanup()
    {
    }

    @Override
    public boolean targetedUpdate(String nextAgentName)
    {
        return false;   // Does nothing.
    }

    @Override
    public void getTurnParticipants(ArrayList<String> participants, ArrayList<Integer> participantSlots)
    {
        // Does nothing.
    }
}
