package com.microsoft.Malmo.MissionHandlers;

import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import com.microsoft.Malmo.MissionHandlerInterfaces.IPerformanceProducer;
import com.microsoft.Malmo.Schemas.FileBasedPerformanceProducer;
import com.microsoft.Malmo.Schemas.MissionInit;
import com.microsoft.Malmo.Utils.PerformanceHelper;

public class FileBasedPerformanceProducerImplementation extends HandlerBase implements IPerformanceProducer {
    private static JsonObject statusJson = new JsonObject();
    private static long WRITE_FREQ = 1000;
    private static String episode_file_name = "";
    static {
        statusJson.addProperty("totalNumberSteps",0);
        statusJson.addProperty("totalNumberEpisodes", 0);
        statusJson.addProperty("currentEnvironment", "NONE");
    }

    private JsonObject currentEpisodeJson;
    
    /**
     * Called  everytime the world is reset.
     */
    @Override
    public void prepare(MissionInit missionInit) {
        String envName = missionInit.getMission().getAbout().getSummary();

        currentEpisodeJson = new JsonObject();
        currentEpisodeJson.addProperty("numTicks", 0);
        currentEpisodeJson.addProperty("environment", envName);
        currentEpisodeJson.addProperty("damageAmount", 0);
        currentEpisodeJson.addProperty("damageSource", "");
        currentEpisodeJson.addProperty("mobName", "");
        currentEpisodeJson.addProperty("deathMessage", "");
        currentEpisodeJson.add("rewards", new JsonArray());

        long numberOfEpisodes = statusJson.get("totalNumberEpisodes").getAsLong();
        episode_file_name = String.format("%06d", numberOfEpisodes) + "-" +  currentEpisodeJson.get("environment").getAsString() + ".json";
        statusJson.addProperty("currentEnvironment", envName);
    }


    @Override
    public boolean parseParameters(Object params)
    {
        if (params == null || !(params instanceof FileBasedPerformanceProducer))
            return false;

        return true;
    }

    @Override
    public void step(double reward, boolean done, JsonObject info) {
        if(PerformanceHelper.performanceEnabled()){
            if(currentEpisodeJson != null && statusJson != null){
                currentEpisodeJson.getAsJsonArray("rewards").add(new JsonPrimitive(reward));
                currentEpisodeJson.addProperty("numTicks", 
                    currentEpisodeJson.get("numTicks").getAsLong() + 1L);

                // Update the damage type
                if (info != null && info.has("damage_source")) {
                    JsonObject damage_source = info.get("damage_source").getAsJsonObject();
                    // Record damage type
                    if (damage_source.has("damage_type")){
                        currentEpisodeJson.addProperty("damageSource",
                                damage_source.get("damage_type").getAsString());
                    }

                    // Record the mob name if any
                    if (damage_source.has("damage_entity")){
                        currentEpisodeJson.addProperty("mobName",
                                damage_source.get("damage_entity").getAsString());
                    }

                    // Accumulate the total damage
                    if (damage_source.has("damage_amount")){
                        currentEpisodeJson.addProperty("damageAmount",
                                currentEpisodeJson.get("damageAmount").getAsFloat() +
                                damage_source.get("damage_amount").getAsFloat());
                    }

                    // Record death message (if any)
                    if (damage_source.has("death_message")){
                        currentEpisodeJson.addProperty("deathMessage",
                                damage_source.get("death_message").getAsString());
                    }

                }


                // Update the global status
                long totalNumberSteps =  statusJson.get("totalNumberSteps").getAsLong();
                statusJson.addProperty("totalNumberSteps",totalNumberSteps + 1L);
                // if(done)
                
                if(done){
                    statusJson.addProperty("totalNumberEpisodes",
                        statusJson.get("totalNumberEpisodes").getAsLong() + 1L);
                }

                // Now we write 
                if(done || (totalNumberSteps % WRITE_FREQ == 0 && totalNumberSteps > 0) ){
                    this.writeJsons();
                }

            }
            else{
                System.out.println("[ERROR] currentEpisodeJson | statusJson is null!");
            }
        } 
    }

    private void writeJsons(){
        // Write the global status json and the rewards json.
        Gson gson = new Gson();
        long numberOfEpisodes = statusJson.get("totalNumberEpisodes").getAsLong();
        
        Path outPath = Paths.get(PerformanceHelper.getOutDir(), episode_file_name );

        try {
            FileWriter file = new FileWriter(outPath.toFile());
            gson.toJson(currentEpisodeJson,file);
            file.close();
        }  catch (IOException e) {
            System.out.println("[ERROR] Failed to episode log for path "+ outPath.toString());
            e.printStackTrace();
        }

        outPath = Paths.get(PerformanceHelper.getOutDir(), "status.json" );

        try {
            FileWriter file = new FileWriter(outPath.toFile());
            gson.toJson(statusJson,file);
            file.close();
        }  catch (IOException e) {
            System.out.println("[ERROR] Failed to episode log for path "+ outPath.toString());
            e.printStackTrace();
        }

    }
}


