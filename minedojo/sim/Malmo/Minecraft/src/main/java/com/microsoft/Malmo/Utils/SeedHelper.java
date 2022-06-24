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

import java.util.ArrayDeque;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

import com.microsoft.Malmo.MalmoMod;
import com.microsoft.Malmo.MalmoMod.IMalmoMessageListener;
import com.microsoft.Malmo.MalmoMod.MalmoMessageType;

import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.item.Item;
import net.minecraftforge.common.config.Configuration;
import net.minecraftforge.event.world.WorldEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.common.gameevent.PlayerEvent.PlayerLoggedInEvent;

@Mod.EventBusSubscriber
public class SeedHelper implements IMalmoMessageListener
{
    private static ArrayDeque<Long> seeds = new ArrayDeque<Long>();
    private static Long currentSeed;
    private static HashMap<String, Random> specificSeedGenerators = new HashMap<String, Random>();
    private static int numRandoms = 0;

    public static Integer mapSeed;

    // The pseudo-random number that is shared across all players
    private static long worldSeed = new Random().nextLong();

    public static SeedHelper instance = new SeedHelper();

    public SeedHelper() {
        MalmoMod.MalmoMessageHandler.registerForMessage(this, MalmoMessageType.SERVER_COMMON_SEED);
    }

    /** Initialize seeding. */
    static public void update(Configuration configs)
    {

        String sSeed = configs.get(MalmoMod.SEED_CONFIGS, "seed", "NONE").getString();
        if(!sSeed.isEmpty() && sSeed != "NONE" ){
            sSeed = sSeed.replaceAll("\\s+","");
            String[] sSeedList =  sSeed.split(",");
                for(int i = 0; i < sSeedList.length; i++){
                try{
                    long seed = Long.parseLong(sSeedList[i]);
                    seeds.push(seed);

                } catch(NumberFormatException e){
                    System.out.println("[ERROR] Seed specified was " + sSeedList[i] + ". Expected a long (integer).");
                }
            } 
        }
    }

    static public Random getRandom(){

        numRandoms +=1;
        return getRandom("");
    } 

    static synchronized public  Random getRandom(String key){
        Random gen = specificSeedGenerators.get(key);

        if(gen == null && currentSeed != null){
            gen = new Random(currentSeed);
            specificSeedGenerators.put(key, gen);
        } else if(currentSeed == null){
            gen = new Random();
        }
        Long seed_inst = (gen.nextLong());
        return new Random(seed_inst);
    }


    @SubscribeEvent
    public static void onWorldCreate(WorldEvent.Load loadEvent){

        loadEvent.getWorld().rand = getRandom(loadEvent.getWorld().toString());
    }

    @SubscribeEvent
    public static void onPlayerLogin(PlayerLoggedInEvent event) {
        MalmoMod.network.sendTo(
                new MalmoMod.MalmoMessage(MalmoMessageType.SERVER_COMMON_SEED, 0,
                        Collections.singletonMap("commonSeed", String.valueOf(worldSeed))),
                (EntityPlayerMP) event.player);

    }

    public static void forceUpdateMinecraftRandoms(){
        Item.itemRand = getRandom("item");
    }

    /**
     * Advances the seed manager to the next seed.
     */
    static public boolean advanceNextSeed(Long nextSeed){
        numRandoms = 0;
        specificSeedGenerators = new HashMap<String, Random>();
        if(seeds.size() > 0){
            currentSeed = seeds.pop();
            forceUpdateMinecraftRandoms();
            if(nextSeed != null){
                System.out.println("[LOGTOPY] Tried to set seed for environment, but overriden by initial seed list.");
                return false;
            } 
        }
        else{

            if(nextSeed != null){
                currentSeed = nextSeed;
                forceUpdateMinecraftRandoms();
            }
            else{
                currentSeed = null;
                forceUpdateMinecraftRandoms();
            }
        }
        return true;
    }

    @Override
    public void onMessage(MalmoMessageType messageType, Map<String, String> data) {
        if (messageType == MalmoMessageType.SERVER_COMMON_SEED) {
            worldSeed = Long.valueOf(data.get("commonSeed"));
        }
    }

    public static long getWorldSeed() {
        return worldSeed;
    }
}