

package com.microsoft.Malmo.Mixins;


import com.google.common.collect.Maps;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.network.NetHandlerPlayServer;
import net.minecraft.network.play.server.SPacketStatistics;
import net.minecraft.stats.StatBase;
import net.minecraft.stats.StatisticsManagerServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.Map;


@Mixin(EntityPlayerMP.class)
public abstract class MixinSyncClientStats {
    // /* Adds additional behavior to onUpdateEntity to sync the statistics tracked on the server
    //  */

    @Shadow public NetHandlerPlayServer connection;
    @Shadow public abstract StatisticsManagerServer getStatFile();

    @Inject(method = "onUpdateEntity", at = @At("TAIL"))
    private void injectSyncStats(CallbackInfo ci) {
        Map<StatBase, Integer> map = Maps.<StatBase, Integer>newHashMap();
        for (StatBase statbase : this.getStatFile().getDirty())
        {
            map.put(statbase, this.getStatFile().readStat(statbase));
        }

        this.connection.sendPacket(new SPacketStatistics(map));
    }


}
