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

import java.util.ArrayList;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import com.microsoft.Malmo.MissionHandlerInterfaces.IWorldDecorator;
import com.microsoft.Malmo.Schemas.AgentSection;
import com.microsoft.Malmo.Schemas.MissionInit;
import com.microsoft.Malmo.Schemas.MarkingDecorator;
import com.microsoft.Malmo.Schemas.PosAndDirection;
import com.microsoft.Malmo.Utils.MinecraftTypeHelper;
import com.microsoft.Malmo.Utils.PositionHelper;
import com.microsoft.Malmo.Utils.SeedHelper;

import net.minecraft.block.state.IBlockState;
import net.minecraft.client.Minecraft;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;
import net.minecraft.world.chunk.Chunk;

/**
 * Creates a decorator that places two distinct "marker" blocks diagonally at world start.
 * Can be used to mark a build area for an agent receiving an exact blueprint to construct.
 *
 * Agent is additionally teleported to a random point within a radius around the marker blocks.
 */
public class MarkingDecoratorImplementation extends HandlerBase implements IWorldDecorator {

	private MarkingDecorator nparams;

	private double originX, originY, originZ;
	private double placementX, placementY, placementZ;
	private double radius;
	private double minRad, maxRad;

	private PosAndDirection startPosition = null;

	@Override
	public boolean parseParameters(Object params) {
		if (params == null || !(params instanceof MarkingDecorator))
			return false;
		this.nparams = (MarkingDecorator) params;
		return true;
	}


	@Override
	public void buildOnWorld(MissionInit missionInit, World world) throws DecoratorException {
		if (nparams.getOrigin() != null)
			originX = nparams.getOrigin().getX().doubleValue();
		else
			originX = world.getSpawnPoint().getX();
		if (nparams.getOrigin() != null)
			originY = nparams.getOrigin().getY().doubleValue();
		else
			originY = world.getSpawnPoint().getY();
		if (nparams.getOrigin() != null)
			originZ = nparams.getOrigin().getZ().doubleValue();
		else
			originZ = world.getSpawnPoint().getZ();

		maxRad = nparams.getMaxRandomizedRadius().doubleValue();
		minRad = nparams.getMinRandomizedRadius().doubleValue();
		radius = (int) (SeedHelper.getRandom().nextDouble() * (maxRad - minRad) + minRad);
		placementX = 0;
		placementY = 0;
		placementZ = 0;
		if (nparams.getPlacement().equals("surface")) {
			placementX = ((SeedHelper.getRandom().nextDouble() - 0.5) * 2 * radius);
			placementZ = (SeedHelper.getRandom().nextDouble() > 0.5 ? -1 : 1) * Math.sqrt((radius * radius) - (placementX * placementX));
			// Change center to origin now
			placementX += originX;
			placementZ += originZ;
			placementY = PositionHelper.getTopTeleportableBlock(world, new BlockPos(placementX, 0, placementZ)).getY();
		} else if (nparams.getPlacement().equals("fixed_surface")) {
			placementX = ((0.42 - 0.5) * 2 * radius);
			placementZ = (0.24 > 0.5 ? -1 : 1) * Math.sqrt((radius * radius) - (placementX * placementX));
			// Change center to origin now
			placementX += originX;
			placementZ += originZ;
			placementY = PositionHelper.getTopTeleportableBlock(world, new BlockPos(placementX, 0, placementZ)).getY();
		} else if (nparams.getPlacement().equals("circle")) {
			placementX = ((SeedHelper.getRandom().nextDouble() - 0.5) * 2 * radius);
			placementY = originY;
			placementZ = (SeedHelper.getRandom().nextDouble() > 0.5 ? -1 : 1) * Math.sqrt((radius * radius) - (placementX * placementX));
			// Change center to origin now
			placementX += originX;
			placementZ += originZ;
		} else {
			placementX = ((SeedHelper.getRandom().nextDouble() - 0.5) * 2 * radius);
			placementY = (SeedHelper.getRandom().nextDouble() - 0.5) * 2 * Math.sqrt((radius * radius) - (placementX * placementX));
			placementZ = (SeedHelper.getRandom().nextDouble() > 0.5 ? -1 : 1)
					* Math.sqrt((radius * radius) - (placementX * placementX) - (placementY * placementY));
			// Change center to origin now
			placementX += originX;
			placementY += originY;
			placementZ += originZ;
		}

		originY = PositionHelper.getTopSolidOrLiquidBlock(world, new BlockPos(originX, 0, originZ)).getY() - 1;

		world.setSpawnPoint(new BlockPos(originX, originY, originZ));

		IBlockState state = MinecraftTypeHelper
				.ParseBlockType(nparams.getBlock1().value());
		world.setBlockState(new BlockPos(originX, originY, originZ), state);

		state = MinecraftTypeHelper
				.ParseBlockType(nparams.getBlock2().value());
		world.setBlockState(new BlockPos(originX+1, originY, originZ+1), state);

		System.out.println(placementX);
		System.out.println(placementY);
		System.out.println(placementZ);
		System.out.println(originX);
		System.out.println(originY);
		System.out.println(originZ);

		teleportAgents(missionInit, world);
	}

	private void teleportAgents(MissionInit missionInit, World world)
    {

        PosAndDirection pos = new PosAndDirection();
        // Force all players to being at a random starting position
        for (AgentSection as : missionInit.getMission().getAgentSection())
        {
            pos.setX(new BigDecimal(placementX + 0.5));
            pos.setY(new BigDecimal(placementY));
            pos.setZ(new BigDecimal(placementZ + 0.5));

            this.startPosition = pos;
            as.getAgentStart().setPlacement(pos);
        }
    }

	@Override
	public boolean getExtraAgentHandlersAndData(List<Object> handlers, Map<String, String> data) {
        // Also add our new start data:
        Float x = this.startPosition.getX().floatValue();
        Float y = this.startPosition.getY().floatValue();
        Float z = this.startPosition.getZ().floatValue();
        String posString = x.toString() + ":" + y.toString() + ":" + z.toString();
        data.put("startPosition", posString);

        return false;
	}

	@Override
	public void update(World world) {
		//if (Minecraft.getMinecraft().player != null) {
		//	BlockPos spawn = Minecraft.getMinecraft().player.world.getSpawnPoint();
		//	if (spawn.getX() != (int) placementX && spawn.getY() != (int) placementY
		//			&& spawn.getZ() != (int) placementZ)
		//		Minecraft.getMinecraft().player.world.setSpawnPoint(new BlockPos(placementX, placementY, placementZ));
		//}
	}

	@Override
	public void prepare(MissionInit missionInit) {
	}

	@Override
	public void cleanup() {
	}

	@Override
	public boolean targetedUpdate(String nextAgentName) {
		return false;
	}

	@Override
	public void getTurnParticipants(ArrayList<String> participants, ArrayList<Integer> participantSlots) {
	}
}