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

import com.microsoft.Malmo.MissionHandlerInterfaces.IWantToQuit;
import com.microsoft.Malmo.Schemas.ServerQuitFromDeath;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.client.Minecraft;
import net.minecraft.entity.player.EntityPlayerMP;

import java.util.Objects;

/**
 * IWantToQuit object that returns true when an agent dies.
 * Also records the reason for death.
 */

public class ServerQuitFromDeathImplementation extends AgentQuitFromDeathImplementation implements IWantToQuit
{
	private ServerQuitFromDeath params = null;
	private Boolean quitWhenAnyDead = true;

	@Override
	public boolean parseParameters(Object params) {
		if (!(params instanceof ServerQuitFromDeath))
			return false;

		this.params = (ServerQuitFromDeath) params;
		this.quitWhenAnyDead = this.params.isQuitWhenAnyDead();
		return true;
	}


	@Override
	public boolean doIWantToQuit(MissionInit missionInit) {
		for (EntityPlayerMP playerMP : Objects.requireNonNull(Minecraft.getMinecraft().getIntegratedServer()).getPlayerList().playerEntityList) {
			if (this.quitWhenAnyDead == playerMP.isDead)
					return this.quitWhenAnyDead;
		}
		return !this.quitWhenAnyDead;
	}

	@Override
    public void prepare(MissionInit missionInit) {}

	@Override
    public void cleanup() {}

}
