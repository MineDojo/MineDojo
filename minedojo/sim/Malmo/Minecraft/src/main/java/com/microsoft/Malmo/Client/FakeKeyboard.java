package com.microsoft.Malmo.Client;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;

public class FakeKeyboard {

    private static Deque<FakeKeyEvent> eventQueue = new ArrayDeque<FakeKeyEvent>();
    private static FakeKeyEvent currentEvent;
    private static Set<Integer> keysDown = new HashSet<Integer>();

    public static boolean next() {
        currentEvent = eventQueue.poll();
        return currentEvent != null;
    }

    public static int getEventKey() {
        return currentEvent.key;
    }

    public static char getEventCharacter() {
        System.out.println("FakeKeyboard - getEventChar is called ");
        return currentEvent.character;
    }

    public static boolean getEventKeyState() {
        return currentEvent.state;
    }

    public static long getEventNanoseconds() {
        return currentEvent.nanos;
    }

    public static boolean isRepeatEvent() {
        return currentEvent.repeat;
    }

    public static final class FakeKeyEvent {
        /** The current keyboard character being examined */
        private final char character;

        /** The current keyboard event key being examined */
        private final int key;

        /** The current state of the key being examined in the event queue */
        private final boolean state;

        /** The current event time */
        private long nanos;

        /** Is the current event a repeated event? */
        private boolean repeat;

        public FakeKeyEvent(char character, int key, boolean state, long nanos, boolean repeat) {
            this.character = character;
            this.key = key;
            this.state = state;
            this.nanos = nanos;
            this.repeat = repeat;
        }

        public FakeKeyEvent(char character, int key, boolean state) {
            this(character, key, state, System.nanoTime(), false);
        }

        public FakeKeyEvent(char character, int key) {
            this(character, key, true);
        }

        public FakeKeyEvent(int key) {
            this((char) 0, key);
        }

    }

    public static void press(int key) {
        if (!keysDown.contains(key)) {
            System.out.println("Pressed " + String.valueOf(key));
            add(new FakeKeyEvent(' ', key, true));
        }
    }

    public static void release(int key) {
        if (keysDown.contains(key)) {
            System.out.println("Released " + String.valueOf(key));
            add(new FakeKeyEvent(' ', key, false));
        }
    }

    public static void add(FakeKeyEvent event) {
        eventQueue.add(event);
        if (event.state) {
            keysDown.add(event.key);
        } else {
            keysDown.remove(event.key);
        }
    }

    public static boolean isKeyDown(int key) {
        return keysDown.contains(key);
    }
}
