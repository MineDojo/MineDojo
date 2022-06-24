package com.microsoft.Malmo.Launcher;

import java.io.File;
import java.lang.reflect.Method;
import java.lang.reflect.Field;
import java.net.Proxy;
import java.util.List;
import java.util.Map;

import com.google.common.base.Strings;
import com.google.common.base.Throwables;
import com.google.gson.GsonBuilder;
import com.mojang.authlib.Agent;
import com.mojang.authlib.exceptions.AuthenticationException;
import com.mojang.authlib.properties.PropertyMap;
import com.mojang.authlib.yggdrasil.YggdrasilAuthenticationService;
import com.mojang.authlib.yggdrasil.YggdrasilUserAuthentication;


public class GradleStart extends GradleStartCommon
{
    public static void main(String[] args) throws Throwable
    {
        // hack natives.
        hackNatives();
        // launch
        (new GradleStart()).launch(args);
    }

    @Override
    protected String getBounceClass()
    {
        return "net.minecraft.launchwrapper.Launch";
    }

    @Override
    protected String getTweakClass()
    {
        return "net.minecraftforge.fml.common.launcher.FMLTweaker";
    }

    @Override
    protected void setDefaultArguments(Map<String, String> argMap)
    {
        argMap.put("version",        "1.11.2");
        argMap.put("assetIndex",     "1.11");
        argMap.put("assetsDir",      MINECRAFT_CACHE_DIR + "assets");
        argMap.put("accessToken",    "FML");
        argMap.put("userProperties", "{}");
        argMap.put("username",        null);
        argMap.put("password",        null);
    }

    @Override
    protected void preLaunch(Map<String, String> argMap, List<String> extras)
    {
        if (!Strings.isNullOrEmpty(argMap.get("password")))
        {
            GradleStartCommon.LOGGER.info("Password found, attempting login");
            attemptLogin(argMap);
        }

        if (!Strings.isNullOrEmpty(argMap.get("assetIndex")))
        {
            //setupAssets(argMap);
        }
    }

    private static void hackNatives()
    {
        String paths = System.getProperty("java.library.path");
        String nativesDir = MINECRAFT_CACHE_DIR + "net/minecraft/natives/1.11.2";

        if (Strings.isNullOrEmpty(paths))
            paths = nativesDir;
        else
            paths += File.pathSeparator + nativesDir;

        System.setProperty("java.library.path", paths);

        // hack the classloader now.
        try
        {
            // force library path re-computation
            final Field sysPathsField = ClassLoader.class.getDeclaredField("sys_paths");
            sysPathsField.setAccessible(true);
            sysPathsField.set(null, null);

            final Method initPaths = ClassLoader.class.getDeclaredMethod("initLibraryPaths");
            initPaths.setAccessible(true);
            initPaths.invoke(null);
        }
        catch(Throwable t) {};
    }

    private void attemptLogin(Map<String, String> argMap)
    {
        YggdrasilUserAuthentication auth = (YggdrasilUserAuthentication) new YggdrasilAuthenticationService(Proxy.NO_PROXY, "1").createUserAuthentication(Agent.MINECRAFT);
        auth.setUsername(argMap.get("username"));
        auth.setPassword(argMap.get("password"));
        argMap.put("password", null);

        try {
            auth.logIn();
        }
        catch (AuthenticationException e)
        {
            LOGGER.error("-- Login failed!  " + e.getMessage());
            Throwables.propagate(e);
            return; // dont set other variables
        }

        LOGGER.info("Login Succesful!");
        argMap.put("accessToken", auth.getAuthenticatedToken());
        argMap.put("uuid", auth.getSelectedProfile().getId().toString().replace("-", ""));
        argMap.put("username", auth.getSelectedProfile().getName());
        argMap.put("userType", auth.getUserType().getName());

        // 1.8 only apperantly.. -_-
        argMap.put("userProperties", new GsonBuilder().registerTypeAdapter(PropertyMap.class, new PropertyMap.Serializer()).create().toJson(auth.getUserProperties()));
    }
}
