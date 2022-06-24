package com.microsoft.Malmo.Mixins;

import java.io.IOException;
import java.util.Queue;
import java.util.concurrent.FutureTask;

import com.microsoft.Malmo.Client.FakeMouse;
import org.lwjgl.opengl.Display;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;
import org.spongepowered.asm.mixin.Shadow;

import com.microsoft.Malmo.Client.PostRenderEvent;
import com.microsoft.Malmo.Utils.TimeHelper;

import net.minecraft.client.Minecraft;
import net.minecraft.client.audio.SoundHandler;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.achievement.GuiAchievement;
import net.minecraft.client.multiplayer.PlayerControllerMP;
import net.minecraft.client.multiplayer.WorldClient;
import net.minecraft.client.renderer.EntityRenderer;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.OpenGlHelper;
import net.minecraft.client.renderer.chunk.RenderChunk;
import net.minecraft.client.settings.GameSettings;
import net.minecraft.client.shader.Framebuffer;
import net.minecraft.network.NetworkManager;
import net.minecraft.profiler.Profiler;
import net.minecraft.profiler.Snooper;
import net.minecraft.server.integrated.IntegratedServer;
import net.minecraft.util.FrameTimer;
import net.minecraft.util.Timer;
import net.minecraft.util.Util;
import net.minecraftforge.client.event.GuiScreenEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.gameevent.TickEvent.Phase;
import scala.collection.parallel.ParIterableLike;

@Mixin(Minecraft.class) 
public abstract class MixinMinecraftGameloop {
    @Shadow public  Profiler mcProfiler;
    @Shadow private SoundHandler mcSoundHandler;
    @Shadow public abstract void shutdown();
    @Shadow public boolean isGamePaused;
    @Shadow public WorldClient world;
    @Shadow public Timer timer;
    @Shadow public  Queue < FutureTask<? >> scheduledTasks;
    @Shadow public abstract void runTick() throws IOException;

    @Shadow public abstract void checkGLError(String message);
    @Shadow public abstract void displayDebugInfo(long elapsedTicksTime);
    @Shadow public EntityPlayerSP player;
    @Shadow private Framebuffer framebufferMc;
    @Shadow public boolean skipRenderWorld;
    @Shadow public EntityRenderer entityRenderer;
    @Shadow public GameSettings gameSettings;
    @Shadow long prevFrameTime;
    @Shadow public GuiAchievement guiAchievement;
    @Shadow int displayWidth;
    @Shadow public PlayerControllerMP playerController;
    @Shadow private NetworkManager myNetworkManager;


    
    @Shadow int displayHeight;
    @Shadow public abstract void updateDisplay();
    @Shadow private int fpsCounter;
    @Shadow public abstract boolean  isSingleplayer();
    @Shadow public GuiScreen currentScreen;
    @Shadow private IntegratedServer theIntegratedServer;
    @Shadow public  FrameTimer frameTimer;
    /** Time in nanoseconds of when the class is loaded */
    @Shadow long startNanoTime;
    @Shadow private long debugUpdateTime;
    @Shadow public String debug;
    @Shadow public Snooper usageSnooper;
    @Shadow public abstract int getLimitFramerate();
    @Shadow public abstract boolean isFramerateLimitBelowMax();
    
    @Shadow public boolean inGameHasFocus; 
    @Shadow private int leftClickCounter; 

    @Shadow public abstract void displayGuiScreen(GuiScreen guiScreen);
    
    private  int numTicksPassed = 0;


    private void runGameLoop() throws IOException
    {

        long i = System.nanoTime();
        this.mcProfiler.startSection("root");

        if (Display.isCreated() && Display.isCloseRequested())
        {
            this.shutdown();
        }


        float f = this.timer.renderPartialTicks;
        if (this.isGamePaused && this.world != null)
        {
            this.timer.updateTimer();
            this.timer.renderPartialTicks = f;
        }
        else
        {
            this.timer.updateTimer();
        }

        this.mcProfiler.startSection("scheduledExecutables");

        synchronized (this.scheduledTasks)
        {
            while (!this.scheduledTasks.isEmpty())
            {
                // TODO: MAke logger public
                Util.runTask((FutureTask)this.scheduledTasks.poll(), Minecraft.LOGGER);
            }
        }

        this.mcProfiler.endSection(); //scheduledExecutables
        long l = System.nanoTime();


        if(TimeHelper.SyncManager.isSynchronous() && !this.isGamePaused ){
            this.mcProfiler.startSection("waitForTick");
            // TimeHelper.SyncManager.debugLog("[Client] Waiting for tick request!");

            TimeHelper.SyncManager.clientTick.awaitRequest(true);


            this.timer.renderPartialTicks = 0;

            this.mcProfiler.endSection();
            this.mcProfiler.startSection("syncTickEventPre");



            MinecraftForge.EVENT_BUS.post(new TimeHelper.SyncTickEvent(Phase.START));
            this.mcProfiler.endSection();
            this.mcProfiler.startSection("clientTick");


            this.runTick();

            // TODO: FIGURE OUT BS WITH 
            // this.timer.renderPartialTicks = f; MAYBE 0 makes something consistent

            this.mcProfiler.endSection(); //ClientTick
         } else{
            for (int j = 0; j < this.timer.elapsedTicks; ++j)
            {
                this.runTick();
            }
        }


        this.mcProfiler.startSection("preRenderErrors");
        long i1 = System.nanoTime() - l;
        this.checkGLError("Pre render");
        this.mcProfiler.endSection();
        this.mcProfiler.startSection("sound");
        this.mcSoundHandler.setListener(this.player, this.timer.renderPartialTicks);
        // this.mcProfiler.endSection();
        this.mcProfiler.endSection();
        this.mcProfiler.startSection("render");


        
        //Speeds up rendering; though it feels necessary. s
        GlStateManager.pushMatrix();
        GlStateManager.clear(16640);
        this.framebufferMc.bindFramebuffer(true);

        this.mcProfiler.startSection("display");
        GlStateManager.enableTexture2D();
        this.mcProfiler.endSection(); //display


        if (!this.skipRenderWorld)
        {
            net.minecraftforge.fml.common.FMLCommonHandler.instance().onRenderTickStart(this.timer.renderPartialTicks);
            this.mcProfiler.endStartSection("gameRenderer");
            this.entityRenderer.updateCameraAndRender(this.timer.renderPartialTicks, i);
            Minecraft mc = Minecraft.getMinecraft();
            MinecraftForge.EVENT_BUS.post(new PostRenderEvent(this.timer.renderPartialTicks));
            this.mcProfiler.endSection();
            net.minecraftforge.fml.common.FMLCommonHandler.instance().onRenderTickEnd(this.timer.renderPartialTicks);
        }

        this.mcProfiler.endSection(); ///root
        if (this.gameSettings.showDebugInfo && this.gameSettings.showDebugProfilerChart && !this.gameSettings.hideGUI)
        {
            if (!this.mcProfiler.profilingEnabled)
            {
                this.mcProfiler.clearProfiling();
            }

        this.mcProfiler.profilingEnabled = true;

            this.displayDebugInfo(i1);
        }
        else
        {
            this.mcProfiler.profilingEnabled = false;
            this.prevFrameTime = System.nanoTime();
        }

        this.guiAchievement.updateAchievementWindow();
        this.framebufferMc.unbindFramebuffer();
        GlStateManager.popMatrix();
        GlStateManager.pushMatrix();
        this.framebufferMc.framebufferRender(this.displayWidth, this.displayHeight);
        GlStateManager.popMatrix();
        GlStateManager.pushMatrix();
        this.entityRenderer.renderStreamIndicator(this.timer.renderPartialTicks);
        GlStateManager.popMatrix();

        this.mcProfiler.startSection("root");
        TimeHelper.updateDisplay();
        // this.updateDisplay();

        if(
            (TimeHelper.SyncManager.isSynchronous())
            // TODO WHY REMOVE 
            // TimeHelper.SyncManager.isServerRunning()
        ){

            this.mcProfiler.startSection("syncTickEventPost");
            MinecraftForge.EVENT_BUS.post(new TimeHelper.SyncTickEvent(Phase.END));
            this.mcProfiler.endSection();
            
            TimeHelper.SyncManager.clientTick.complete();
        }
        Thread.yield();
        this.checkGLError("Post render");
        ++this.fpsCounter;
        this.isGamePaused = this.isSingleplayer() && this.currentScreen != null && this.currentScreen.doesGuiPauseGame() && !this.theIntegratedServer.getPublic();
        long k = System.nanoTime();
        this.frameTimer.addFrame(k - this.startNanoTime);
        this.startNanoTime = k;

        while (Minecraft.getSystemTime() >= this.debugUpdateTime + 1000L)
        {
            // TODO: Add to CFG and make public.
            Minecraft.debugFPS = this.fpsCounter;
            this.debug = String.format("%d fps (%d chunk update%s) T: %s%s%s%s%s", new Object[] {Integer.valueOf(Minecraft.debugFPS), Integer.valueOf(RenderChunk.renderChunksUpdated), RenderChunk.renderChunksUpdated == 1 ? "" : "s", (float)this.gameSettings.limitFramerate == GameSettings.Options.FRAMERATE_LIMIT.getValueMax() ? "inf" : Integer.valueOf(this.gameSettings.limitFramerate), this.gameSettings.enableVsync ? " vsync" : "", this.gameSettings.fancyGraphics ? "" : " fast", this.gameSettings.clouds == 0 ? "" : (this.gameSettings.clouds == 1 ? " fast-clouds" : " fancy-clouds"), OpenGlHelper.useVbo() ? " vbo" : ""});
            RenderChunk.renderChunksUpdated = 0;
            this.debugUpdateTime += 1000L;
            this.fpsCounter = 0;
            this.usageSnooper.addMemoryStatsToSnooper();

            if (!this.usageSnooper.isSnooperRunning())
            {
                this.usageSnooper.startSnooper();
            }
        }

        if (this.isFramerateLimitBelowMax() && !TimeHelper.SyncManager.isSynchronous())
        {
            this.mcProfiler.startSection("fpslimit_wait");
            Display.sync(this.getLimitFramerate());
            this.mcProfiler.endSection();
        }

        this.mcProfiler.endSection(); //root
    }
    
    @Overwrite
    public void setIngameFocus()
    {
        if (!this.inGameHasFocus) {
            this.inGameHasFocus = true;
            this.displayGuiScreen((GuiScreen) null);
            this.leftClickCounter = 10000;
        }
    }

}