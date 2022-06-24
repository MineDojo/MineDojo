package com.microsoft.Malmo.MissionHandlers;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityLivingBase;
import net.minecraft.item.ItemStack;
import net.minecraft.util.DamageSource;
import net.minecraft.util.math.Vec3d;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

import static java.lang.Math.asin;
import static java.lang.Math.atan2;
import java.lang.Math;

/**
 * Simple IObservationProducer object that pings out a whole bunch of data.<br>
 */
public class ObservationFromDamageImplementation extends HandlerBase implements IObservationProducer {
    private DamageSource damageSource;
    private float damageAmount;
    private boolean hasDied = false;
    private boolean damageSourceReplaced = false;


    @Override
    public void prepare(MissionInit missionInit) {
        MinecraftForge.EVENT_BUS.register(this);
    }

    @Override
    public void cleanup() {
    }

    @SubscribeEvent
    public void onDeath(LivingDeathEvent event) {
        if (event.getEntityLiving().equals(Minecraft.getMinecraft().player)) {
            if (this.damageSource != null) {
                // If the agent dies from damage, a LivingHurtEvent will precede the death event. Since death events do
                // not include the damage amount we simply update the other fields to ensure the cause of death is
                // properly reflected
                this.damageSourceReplaced = true;
            }
            this.damageSource = event.getSource();
            this.hasDied = true;
        }
    }

    @SubscribeEvent
    public void onDamage(LivingHurtEvent event) {
        if (event.getEntityLiving().equals(Minecraft.getMinecraft().player)) {
            if (this.damageSource != null) {
                this.damageSourceReplaced = true;
                // If multiple LivingHurtEvents pertain to the player, we keep the most recent one and record the fact
                // that we are skipping a damage event in lieu of building an array based reporting system
                System.out.println("Warning skipped damage event - multiple damage events in one tick!");
                System.out.println("This damage event will be marked as stale=True.");
            }
            this.damageSource = event.getSource();
            this.damageAmount = event.getAmount();
        }
    }

    private void resetDamage() {
        this.damageAmount = 0;
        this.damageSource = null;
        this.hasDied = false;
        this.damageSourceReplaced = false;
    }

    @Override
    public void writeObservationsToJSON(JsonObject json, MissionInit missionInit) {
        EntityPlayerSP player = Minecraft.getMinecraft().player;
        JsonObject damage_json = new JsonObject();
        json.addProperty("is_dead", player.isDead);
        json.addProperty("living_death_event_fired", this.hasDied);

        // Note to user that there could be inaccuracies here
//        if (this.damageSourceReplaced) {
//            damage_json.addProperty("stale", true);
//        }

//        if (this.damageAmount != 0 && this.damageSource != null) {
//            System.out.println(this.damageAmount + " damage from " + this.damageSource.getDamageType() + " by entity " + this.damageSource.getEntity());
//        }

//        if (this.damageAmount != 0) {
//            damage_json.addProperty("damage_amount", this.damageAmount);
//        }
        damage_json.addProperty("damage_amout", this.damageAmount);

        if (this.damageSource != null) {
//            damage_json.addProperty("damage_type", this.damageSource.getDamageType());
            damage_json.addProperty("hunger_damage", this.damageSource.getHungerDamage());
//            damage_json.addProperty("is_damage_absolute", this.damageSource.isDamageAbsolute());
            damage_json.addProperty("is_fire_damage", this.damageSource.isFireDamage());
            damage_json.addProperty("is_magic_damage", this.damageSource.isMagicDamage());
//            damage_json.addProperty("is_difficulty_scaled", this.damageSource.isDifficultyScaled());
            damage_json.addProperty("is_explosion", this.damageSource.isExplosion());
            damage_json.addProperty("is_projectile", this.damageSource.isProjectile());
            damage_json.addProperty("is_unblockable", this.damageSource.isUnblockable());
//            damage_json.addProperty("death_message", this.damageSource.getDeathMessage(player).getUnformattedText());

//            if (this.damageSource.getEntity() != null) {
//                Entity entity = this.damageSource.getEntity();
//                damage_json.addProperty("damage_entity", entity.getName());
//                damage_json.addProperty("damage_entity_id", entity.getEntityId());
//                JsonArray entity_equipment = new JsonArray();
//                // TODO do we need to mark the equipment slot of this armor?
//                for (ItemStack item : entity.getEquipmentAndArmor()) {
//                    if (item.getItem().getRegistryName() != null) {
//                        JsonElement jitem = new JsonPrimitive(item.getItem().getRegistryName().toString());
//                        entity_equipment.add(jitem);
//                    }
//                }
//                damage_json.add("damage_entity_equipment", entity_equipment);
//            }
            if (this.damageSource.getDamageLocation() != null) {
//                damage_json.addProperty("damage_location", this.damageSource.getDamageLocation().toString());
                damage_json.addProperty("damage_distance", this.damageSource.getDamageLocation().distanceTo(player.getPositionVector()));
                Vec3d attack_vec = this.damageSource.getDamageLocation().subtract(player.getPositionVector());
                damage_json.addProperty("damage_pitch", asin(attack_vec.yCoord) * 180.0 / Math.PI);
                damage_json.addProperty("damage_yaw", atan2(attack_vec.xCoord, attack_vec.zCoord)  * 180.0 / Math.PI);
            }
            else {
                damage_json.addProperty("damage_distance", 0);
                damage_json.addProperty("damage_pitch", 0);
                damage_json.addProperty("damage_yaw", 0);
            }
        }
        else {
            damage_json.addProperty("hunger_damage", 0);
            damage_json.addProperty("is_fire_damage", false);
            damage_json.addProperty("is_magic_damage", false);
            damage_json.addProperty("is_explosion", false);
            damage_json.addProperty("is_projectile", false);
            damage_json.addProperty("is_unblockable", false);
            damage_json.addProperty("damage_distance", 0);
            damage_json.addProperty("damage_pitch", 0);
            damage_json.addProperty("damage_yaw", 0);
        }

        // Ensure we only report damage / death once
        this.resetDamage();

        json.add("damage_source", damage_json);
    }

}
