package com.microsoft.Malmo.Launcher;

import java.util.List;
import java.util.Map;

public class GradleStartServer extends GradleStartCommon
{
    public static void main(String[] args) throws Throwable
    {
        (new GradleStartServer()).launch(args);
    }

    @Override
    protected String getTweakClass()
    {
        return "net.minecraftforge.fml.common.launcher.FMLServerTweaker";
    }

    @Override
    protected String getBounceClass()
    {
       return "net.minecraft.launchwrapper.Launch";
    }

    @Override protected void preLaunch(Map<String, String> argMap, List<String> extras) { }
    @Override protected void setDefaultArguments(Map<String, String> argMap) { }
}
