

package com.microsoft.Malmo.Mixins;


import java.util.Iterator;
import java.util.Random;
import java.util.Set;

import com.microsoft.Malmo.Utils.SeedHelper;
import com.microsoft.Malmo.Utils.TimeHelper;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.Overwrite;

import net.minecraft.client.renderer.chunk.ChunkRenderDispatcher;
import net.minecraft.client.renderer.chunk.RenderChunk;
import net.minecraft.client.renderer.RenderGlobal;


@Mixin(RenderGlobal.class)
public abstract class MixinUpdateChunksNoTimeout  {
    // /* Overrides methods within the RenderGlobal class.
    //  */

    @Shadow private boolean displayListEntitiesDirty;
    @Shadow private ChunkRenderDispatcher renderDispatcher;
    @Shadow private Set<RenderChunk> chunksToUpdate;

    @Overwrite
    public void updateChunks(long finishTimeNano)
    {
        // This is the implementation of updateChunks as of 1.11, with some code removed
        this.displayListEntitiesDirty |= this.renderDispatcher.runChunkUploads(finishTimeNano);

        if (!this.chunksToUpdate.isEmpty())
        {
            Iterator<RenderChunk> iterator = this.chunksToUpdate.iterator();

            while (iterator.hasNext())
            {
                RenderChunk renderchunk = (RenderChunk)iterator.next();
                boolean flag;

                flag = this.renderDispatcher.updateChunkNow(renderchunk);

                if (!flag)
                {
                    break;
                }

                renderchunk.clearNeedsUpdate();
                iterator.remove();

                long i = finishTimeNano - System.nanoTime();
            }
        }
    }

}
