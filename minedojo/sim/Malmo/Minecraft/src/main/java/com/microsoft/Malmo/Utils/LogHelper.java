package com.microsoft.Malmo.Utils;
import java.util.HashSet;

public class LogHelper {

    private static HashSet<Integer> silenced = new HashSet<Integer>();

    public static void debug(String message) {
        System.out.println("[DEBUG] " + message);
    }

    public static void debugOnce(String message) {
        // only show once
        int hashCode = hashCaller();
        if (silenced.contains(hashCode)) {
            return;
        }
        silenced.add(hashCode);

        debug(message);
    }

    public static void error(String message) {
        System.err.println("[DEBUG] " + message);
    }

    public static void error(String message, Exception e) {
        if (e != null) {
            message += ": " + e;
        }

        error(message);

        e.printStackTrace(System.err);
    }

    private static int hashCaller() {
        StackTraceElement[] stackTraceElements = Thread.currentThread().getStackTrace();
        // skip calls: getStackTrace, hashCaller
        StackTraceElement ste = stackTraceElements[2];
        return (ste.getClassName() + "." + ste.getMethodName()).hashCode();
    }

}
