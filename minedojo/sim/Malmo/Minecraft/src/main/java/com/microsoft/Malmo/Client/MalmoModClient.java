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

package com.microsoft.Malmo.Client;

import net.minecraft.client.gui.GuiGameOver;
import net.minecraftforge.fml.common.eventhandler.Event;
import java.io.IOException;
import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.lwjgl.input.Mouse;

import com.microsoft.Malmo.Utils.CraftingHelper;
import com.microsoft.Malmo.Utils.ScreenHelper.TextCategory;
import com.microsoft.Malmo.Utils.TextureHelper;

import net.minecraft.block.BlockContainer;
import net.minecraft.block.BlockWorkbench;
import net.minecraft.block.state.IBlockState;
import net.minecraft.client.Minecraft;
import net.minecraft.client.settings.GameSettings;
import net.minecraft.entity.item.EntityMinecartCommandBlock;
import net.minecraft.entity.item.EntityMinecartContainer;
import net.minecraft.entity.passive.EntityVillager;
import net.minecraft.util.MouseHelper;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.RayTraceResult;
import net.minecraftforge.client.event.GuiOpenEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.fml.common.event.FMLInitializationEvent;
import net.minecraftforge.fml.common.eventhandler.EventPriority;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.relauncher.Side;
import net.minecraftforge.fml.relauncher.SideOnly;

public class MalmoModClient
{
    
    public interface MouseEventListener
    {
        public void onXYZChange(int deltaX, int deltaY, int deltaZ);
    }

    public class MouseHook extends MouseHelper
    {
        public boolean isOverriding = true;
        private MouseEventListener observer = null;

		/* (non-Javadoc)
         * @see net.minecraft.util.MouseHelper#mouseXYChange()
         * If we are overriding control, don't allow Minecraft to do any of the usual camera/yaw/pitch stuff that happens when the mouse moves.
         */
        @Override
        public void mouseXYChange()
        {
            if (this.isOverriding)
            {
                this.deltaX = 0;
                this.deltaY = 0;
                if (Mouse.isGrabbed())
                    Mouse.setGrabbed(false);
            }
            else
            {
                super.mouseXYChange();
                if (this.observer != null)
                    this.observer.onXYZChange(this.deltaX, this.deltaY, Mouse.getDWheel());
            }
        }

        @Override
        public void grabMouseCursor()
        {
            if (MalmoModClient.this.inputType != InputType.HUMAN)
            {
                return;
            }
            super.grabMouseCursor();
        }
    
        @Override
        /**
         * Ungrabs the mouse cursor so it can be moved and set it to the center of the screen
         */
        public void ungrabMouseCursor()
        {
            // Vanilla Minecraft calls Mouse.setCursorPosition(Display.getWidth() / 2, Display.getHeight() / 2) at this point...
            // but it's seriously annoying, so we don't.
            Mouse.setGrabbed(false);
        }

        public void requestEvents(MouseEventListener observer)
        {
            this.observer = observer;
        }
    }
    
    // Control overriding:
    enum InputType
    {
        HUMAN, AI
    }

    protected InputType inputType = InputType.HUMAN;
    protected MouseHook mouseHook;
    protected MouseHelper originalMouseHelper;
	private KeyManager keyManager;
	private ClientStateMachine stateMachine;
	private static final String INFO_MOUSE_CONTROL = "mouse_control";

	public void init(FMLInitializationEvent event)
	{
        // Register for various events:
        MinecraftForge.EVENT_BUS.register(this);
        GameSettings settings = Minecraft.getMinecraft().gameSettings;
        TextureHelper.hookIntoRenderPipeline();
        setUpExtraKeys(settings);

        this.stateMachine = new ClientStateMachine(ClientState.WAITING_FOR_MOD_READY, this);

        this.originalMouseHelper = Minecraft.getMinecraft().mouseHelper;
        this.mouseHook = new MouseHook();
        this.mouseHook.isOverriding = true;
        // TODO MouseHook is disabled. It is currently used in ObservationFromHumanImplementation
        // which is decprectated? way of passing human-level commands and (may?) have been used for recording
        // Minecraft.getMinecraft().mouseHelper = this.mouseHook;
        setInputType(InputType.AI);
    }

    /** Switch the input type between Human and AI.<br>
     * Will switch on/off the command overrides.
     * @param input type of control (Human/AI)
     */
    public void setInputType(InputType input)
    {
    	if (this.stateMachine.currentMissionBehaviour() != null && this.stateMachine.currentMissionBehaviour().commandHandler != null)
    		this.stateMachine.currentMissionBehaviour().commandHandler.setOverriding(input == InputType.AI);

    	if (this.mouseHook != null)
    		this.mouseHook.isOverriding = (input == InputType.AI);

        // This stops Minecraft from doing the annoying thing of stealing your mouse.
        System.setProperty("fml.noGrab", input == InputType.AI ? "true" : "false");
        inputType = input;
        if (input == InputType.HUMAN)
        {
            Minecraft.getMinecraft().mouseHelper.grabMouseCursor();
        }
        else
        {
            Minecraft.getMinecraft().mouseHelper.ungrabMouseCursor();
        }

		this.stateMachine.getScreenHelper().addFragment("Mouse: " + input, TextCategory.TXT_INFO, INFO_MOUSE_CONTROL);
    }

    
    /** Set up some handy extra keys:
     * @param settings Minecraft's original GameSettings object
     */
    private void setUpExtraKeys(GameSettings settings)
    {
        // Create extra key bindings here and pass them to the KeyManager.
        ArrayList<InternalKey> extraKeys = new ArrayList<InternalKey>();
        // Create a key binding to toggle between player and Malmo control:
        extraKeys.add(new InternalKey("key.toggleMalmo", 28, "key.categories.malmo")	// 28 is the keycode for enter.
        {
            @Override
            public void onPressed()
            {
                InputType it = (inputType != InputType.AI) ? InputType.AI : InputType.HUMAN;
                System.out.println("Toggling control between human and AI - now " + it);
                setInputType(it);
                super.onPressed();
            }
        });

        extraKeys.add(new InternalKey("key.handyTestHook", 22, "key.categories.malmo")
        {
            @Override
            public void onPressed()
            {
                // TODO (R): This is a really janky way of extracting constants. This should 
                // just happen from the command line. -_-
                // Use this if you want to test some code with a handy key press
                CraftingHelper.dumpMinecraftObjectRules("../../../herobraine/hero/mc_constants.json");
            }
        });
        this.keyManager = new KeyManager(settings, extraKeys);
    }

    /**
     * Event listener that prevents agents from opening gui windows by canceling the 'USE' action of a block
     * deny (most) blocks that open a gui when {@link net.minecraft.block.Block#onBlockActivated} is called
     * @param event the captured event
     */
    @SideOnly(Side.CLIENT)
    @SubscribeEvent(priority = EventPriority.HIGH)
    public void onRightClickEvent(PlayerInteractEvent.RightClickBlock event){
        if(this.stateMachine.getStableState() == ClientState.RUNNING){
            Logger logger = Logger.getLogger("MalmoModClient.onRightClickEvent");
            Minecraft mc = Minecraft.getMinecraft();
            if (mc.objectMouseOver.typeOfHit.equals(RayTraceResult.Type.BLOCK)) {
                BlockPos blockpos = mc.objectMouseOver.getBlockPos();
                IBlockState blockState = mc.world.getBlockState(blockpos);
                if ((!isLowLevelInput()) && (blockState.getBlock() instanceof BlockContainer
                || blockState.getBlock() instanceof BlockWorkbench)){
                    event.setUseBlock(Event.Result.DENY);
                    logger.log(Level.INFO, "Denied usage of " + blockState.getBlock().getRegistryName().toString());
                }
            } else if (mc.objectMouseOver.typeOfHit.equals(RayTraceResult.Type.ENTITY)) {
                // This does not seem to be possible given the case logic in Minecraft.java @ line 1585
                // Included here in the event objectMouseOver changes between these cases
                if (mc.objectMouseOver.entityHit instanceof EntityVillager
                || mc.objectMouseOver.entityHit instanceof EntityMinecartContainer
                || mc.objectMouseOver.entityHit instanceof EntityMinecartCommandBlock) {
                    event.setUseBlock(Event.Result.DENY);
                    logger.log(Level.SEVERE, "Denied usage of " + mc.objectMouseOver.entityHit.getName() + "! This" +
                            "is not expected to happen!");
                }

            }
        }
    }

    public boolean isLowLevelInput() {
        return stateMachine.currentMissionBehaviour().lowLevelInputs;
    }

}
