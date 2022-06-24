package com.microsoft.Malmo.Client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.block.model.ItemCameraTransforms;
import net.minecraft.client.renderer.texture.SimpleTexture;
import net.minecraft.client.renderer.texture.TextureManager;
import net.minecraft.client.renderer.texture.TextureMap;
import net.minecraft.client.resources.FolderResourcePack;
import net.minecraft.client.resources.IResourceManager;
import net.minecraft.client.resources.IResourcePack;
import net.minecraft.client.resources.SimpleReloadableResourceManager;
import net.minecraft.util.ResourceLocation;
import net.minecraftforge.client.event.GuiScreenEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

import java.io.File;

public class FakeMouseCursor {
    FakeMouseCursor() {
        System.out.println("*** creating fake mouse cursor ***");
        register();
    }

    private void register() {
        MinecraftForge.EVENT_BUS.register(this);
    }

    @SubscribeEvent
    public void onScreenDraw(GuiScreenEvent.DrawScreenEvent.Post event) {
        GlStateManager.enableTexture2D();
        GlStateManager.disableLighting();
        GlStateManager.disableDepth();
        GuiScreen screen = event.getGui();
        if (screen == null) {
            return;
        }
        GlStateManager.pushMatrix();
        bindTexture();
        GlStateManager.enableRescaleNormal();
        GlStateManager.enableAlpha();
        GlStateManager.alphaFunc(516, 0.1F);
        GlStateManager.enableBlend();
        GlStateManager.blendFunc(GlStateManager.SourceFactor.SRC_ALPHA, GlStateManager.DestFactor.ONE_MINUS_SRC_ALPHA);
        GlStateManager.color(1.0F, 1.0F, 1.0F, 1.0F);
        screen.drawTexturedModalRect(event.getMouseX(), event.getMouseY(), 0, 0, 16, 16);
        GlStateManager.disableAlpha();
        GlStateManager.disableRescaleNormal();
        GlStateManager.disableLighting();
        GlStateManager.popMatrix();

    }


    private static void bindTexture () {
        TextureManager tm = Minecraft.getMinecraft().getTextureManager();
        IResourceManager rm = Minecraft.getMinecraft().getResourceManager();
        ResourceLocation texLocation = new ResourceLocation("malmopack:mouse_cursor_white_16x16.png");
        if (tm.getTexture(texLocation) == null) {
            IResourcePack resourcePack = new FolderResourcePack(new File("../src/main/resources"));
            ((SimpleReloadableResourceManager)rm).reloadResourcePack(resourcePack);
            SimpleTexture texture = new SimpleTexture(texLocation);
            tm.loadTexture(texLocation, texture);
        }
        tm.bindTexture(texLocation);
        tm.getTexture(texLocation).setBlurMipmap(false, false);
    }
}
