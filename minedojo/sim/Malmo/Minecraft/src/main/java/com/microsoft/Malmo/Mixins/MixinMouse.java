package com.microsoft.Malmo.Mixins;

import org.lwjgl.input.Mouse;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;

import com.microsoft.Malmo.Client.FakeMouse;

@Mixin(Mouse.class)
public abstract class MixinMouse {
    @Overwrite(remap = false)
    public static boolean isCreated() {
        return true;
    }

    @Overwrite(remap = false)
    public static void poll() {

    }

    @Overwrite(remap = false)
    public static void setGrabbed(boolean grabbed) {
        FakeMouse.setGrabbed(grabbed);
    }

    @Overwrite(remap = false)
    public static boolean next() {
        return FakeMouse.next();
    }

    @Overwrite(remap = false)
    public static int getX() {
        return FakeMouse.getX();
    }

    @Overwrite(remap = false)
    public static int getY() {
        return FakeMouse.getY();
    }

    @Overwrite(remap = false)
    public static int getDX() {
        return FakeMouse.getDX();
    }

    @Overwrite(remap = false)
    public static int getDY() {
        return FakeMouse.getDY();
    }

    @Overwrite(remap = false)
    public static int getEventButton() {
        return FakeMouse.getEventButton();
    }

    @Overwrite(remap = false)
    public static boolean getEventButtonState() {
        return FakeMouse.getEventButtonState();
    }

    @Overwrite(remap = false)
    public static int getEventX() {
        return FakeMouse.getEventX();
    }

    @Overwrite(remap = false)
    public static int getEventY() {
        return FakeMouse.getEventY();
    }

    @Overwrite(remap = false)
    public static int getEventDX() {
        return FakeMouse.getEventDX();
    }

    @Overwrite(remap = false)
    public static int getEventDY() {
        return FakeMouse.getEventDY();
    }

    @Overwrite(remap = false)
    public static int getEventDWheel() {
        return FakeMouse.getEventDWheel();
    }

    @Overwrite(remap = false)
    public static long getEventNanoseconds() {
        return FakeMouse.getEventNanoseconds();
    }

    @Overwrite(remap = false)
    public static boolean isButtonDown(int button) {
        return FakeMouse.isButtonDown(button);
    }

    @Overwrite(remap = false)
    public static boolean isInsideWindow() {
        return FakeMouse.isInsideWindow();
    }

    @Overwrite(remap = false)
    public static void setCursorPosition(int newX, int newY) {
        FakeMouse.setCursorPosition(newX, newY);
    }



}