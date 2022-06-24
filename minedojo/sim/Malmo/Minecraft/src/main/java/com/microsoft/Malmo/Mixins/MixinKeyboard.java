package com.microsoft.Malmo.Mixins;

import org.lwjgl.input.Keyboard;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;

import com.microsoft.Malmo.Client.FakeKeyboard;

@Mixin(Keyboard.class)
public abstract class MixinKeyboard {

    @Overwrite(remap = false)
    public static boolean isCreated() {
        return true;
    }

    @Overwrite(remap = false)
    public static void poll() {

    }

    @Overwrite(remap = false)
    public static boolean isKeyDown(int key) {
        return FakeKeyboard.isKeyDown(key);
    }

    @Overwrite(remap = false)
    public static boolean next() {
        return FakeKeyboard.next();
    }

    @Overwrite(remap = false)
    public static int getEventKey() {
        return FakeKeyboard.getEventKey();
    }

    @Overwrite(remap = false)
    public static char getEventCharacter() {
        return FakeKeyboard.getEventCharacter();
    }

    @Overwrite(remap = false)
    public static boolean getEventKeyState() {
        return FakeKeyboard.getEventKeyState();
    }

    @Overwrite(remap = false)
    public static long getEventNanoseconds() {
        return FakeKeyboard.getEventNanoseconds();
    }

    @Overwrite(remap = false)
    public static boolean isRepeatEvent() {
        return FakeKeyboard.isRepeatEvent();
    }


}