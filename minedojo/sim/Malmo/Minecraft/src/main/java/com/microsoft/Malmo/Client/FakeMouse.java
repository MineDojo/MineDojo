package com.microsoft.Malmo.Client;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.inventory.GuiContainer;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.texture.SimpleTexture;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.renderer.texture.TextureManager;
import net.minecraft.client.resources.FolderResourcePack;
import net.minecraft.client.resources.IResourceManager;
import net.minecraft.client.resources.IResourcePack;
import net.minecraft.client.resources.SimpleReloadableResourceManager;
import net.minecraft.util.ResourceLocation;
import net.minecraftforge.client.model.ModelLoader;

import java.io.File;
import java.io.IOException;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;

public class FakeMouse {
    private static int x;
    private static int y;
    private static int dx;
    private static int dy;
    private static int dwheel;

    private static int accumDx;
    private static int accumDy;
    private static int accumDwheel;

    private static Deque<FakeMouseEvent> eventQueue = new ArrayDeque<FakeMouseEvent>();
    private static FakeMouseEvent currentEvent;
    private static Set<Integer> pressedButtons = new HashSet<Integer>();
    private static Set<Integer> accumPressedButtons = new HashSet<Integer>();

    private static boolean grabbed = false;
    private static boolean humanInput = true;

    // private static FakeMouseCursor cursor = new FakeMouseCursor();


    public static void setHumanInput(boolean humanInput) {
        FakeMouse.humanInput = humanInput;
    }

    public static boolean isHumanInput() {
        return humanInput;
    }

    public static JsonElement getState() {
        JsonObject retVal = new JsonObject();
        retVal.addProperty("x", x);
        retVal.addProperty("y", y);
        retVal.addProperty("dx", accumDx);
        retVal.addProperty("dy", accumDy);
        retVal.addProperty("dwheel", accumDwheel);
        retVal.add("buttons", new Gson().toJsonTree(FakeMouse.accumPressedButtons.toArray()));
        accumPressedButtons.retainAll(pressedButtons);
        accumDx = 0;
        accumDy = 0;
        accumDwheel = 0;
        return retVal;
    }

    public static class FakeMouseEvent {
        private int button;

        private boolean state;

        private int dx;
        private int dy;
        private int dwheel;

        private int x;
        private int y;
        private long nanos;

        public FakeMouseEvent(int x, int y, int dx, int dy, int dwheel, int button, boolean state, long nanos) {
            this.x = x;
            this.y = y;
            this.dx = dx;
            this.dy = dy;
            this.button = button;
            this.dwheel = dwheel;
            this.state = state;
            this.nanos = nanos;
        }

        public static FakeMouseEvent move(int dx, int dy) {
            return new FakeMouseEvent((int) FakeMouse.x + dx, (int) FakeMouse.y + dy, dx, dy, 0, -1, false, System.nanoTime());
        }
    }

    public static boolean next() {
        currentEvent = eventQueue.poll();
        return currentEvent != null;

    }

    public static int getX() {
        return (int) x;
    }

    public static int getY() {
        return (int) y;
    }

    public static int getDX() {
        int retval = dx;
        dx = 0;
        return retval;
    }

    public static int getDY() {
        int retval = dy;
        dy = 0;
        return retval;
    }

    public static int getDWheel() {
        int retval = dwheel;
        dwheel = 0;
        return retval;
    }

    public static int getEventButton() {
        if (currentEvent != null) {
            return currentEvent.button;
        } else {
            return -1;
        }
    }

    public static boolean getEventButtonState() {
        if (currentEvent != null) {
            return currentEvent.state;
        } else {
            return false;
        }
    }

    public static int getEventX() {
        return currentEvent.x;
    }

    public static int getEventY() {
        if (currentEvent != null) {
            return currentEvent.y;
        } else {
            return 0;
        }
    }

    public static int getEventDX() {
        if (currentEvent != null) {
            return currentEvent.dx;
        } else {
            return 0;
        }
    }

    public static int getEventDY() {
        if (currentEvent != null) {
            return currentEvent.dy;
        } else {
            return 0;
        }
    }

    public static int getEventDWheel() {
        if (currentEvent != null) {
            return currentEvent.dwheel;
        } else {
            return 0;
        }
    }

    public static long getEventNanoseconds() {
        if (currentEvent != null) {
            return currentEvent.nanos;
        } else {
            return 0;
        }
    }

    public static void addEvent(FakeMouseEvent event) {
        if (event.state) {
            pressedButtons.add(event.button);
            accumPressedButtons.add(event.button);
        } else {
            pressedButtons.remove(event.button);
        }
        dx += event.dx;
        dy += event.dy;
        accumDx += event.dx;
        accumDy += event.dy;
        x = event.x;
        y = event.y;
        eventQueue.add(event);
    }

    public static void pressButton(int button) {
        if (!pressedButtons.contains(button)) {
            System.out.println("Button " + String.valueOf(button) + " is pressed");
            addEvent(new FakeMouseEvent(x, y, 0, 0, 0,  button, true, System.nanoTime()));
        }
    }

    public static void releaseButton(int button) {
        // TODO - match the press event and add dx, dy? Is that necessary?
        if (pressedButtons.contains(button)) {
            System.out.println("Button " + String.valueOf(button) + " is released");
            addEvent(new FakeMouseEvent(x, y, 0, 0, 0, button, false, System.nanoTime()));
        }
    }

    public static void addMovement(int dx, int dy) {
        // split the movement into smaller, one-pixel movements
        // to help drag-splitting calculator find the start of the trajectory
        int stepX = (int) Math.signum(dx);
        int stepY = (int) Math.signum(dy);
        int curDx = 0;
        int curDy = 0;

        while (curDx != dx || curDy != dy) {
            if (curDx != dx) {
                addEvent(FakeMouseEvent.move(stepX, 0));
                curDx += stepX;
            }
            if (curDy != dy) {
                addEvent(FakeMouseEvent.move(0, stepY));
                curDy += stepY;
            }
        }
    }

    public static boolean isButtonDown(int button) {
        return pressedButtons.contains(button);
    }


    public static boolean isInsideWindow() {
        return true;
    }

    public static void setCursorPosition(int newX, int newY) {
        x = newX;
        y = newY;
    }

    public static void setGrabbed(boolean grabbed) {
        FakeMouse.grabbed = grabbed;
    }

    public static boolean isGrabbed() {
        return grabbed;
    }
}
