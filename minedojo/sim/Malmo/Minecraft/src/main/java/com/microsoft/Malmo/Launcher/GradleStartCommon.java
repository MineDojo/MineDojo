/*
 * A Gradle plugin for the creation of Minecraft mods and MinecraftForge plugins.
 * Copyright (C) 2013 Minecraft Forge
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
 * USA
 */
package com.microsoft.Malmo.Launcher;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.google.common.base.Strings;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

import joptsimple.NonOptionArgumentSpec;
import joptsimple.OptionParser;
import joptsimple.OptionSet;

public abstract class GradleStartCommon
{
    protected static Logger LOGGER        = LogManager.getLogger("GradleStart");

    Map<String, String>     argMap        = Maps.newHashMap();
    List<String>            extras        = Lists.newArrayList();

    static final String     MINECRAFT_CACHE_DIR = System.getProperty("com.microsoft.Malmo.GradleStartCommon.minecraftCacheDir", System.getenv("GRADLE_USER_HOME") + "/caches/minecraft/");
    static final File       SRG_DIR       = new File(MINECRAFT_CACHE_DIR + "de/oceanlabs/mcp/mcp_snapshot/20161220/srgs");
    static final File       SRG_NOTCH_SRG = new File(MINECRAFT_CACHE_DIR + "de/oceanlabs/mcp/mcp_snapshot/20161220/1.11.2/srgs/notch-srg.srg");
    static final File       SRG_NOTCH_MCP = new File(MINECRAFT_CACHE_DIR + "de/oceanlabs/mcp/mcp_snapshot/20161220/1.11.2/srgs/notch-mcp.srg");
    static final File       SRG_SRG_MCP   = new File(MINECRAFT_CACHE_DIR + "de/oceanlabs/mcp/mcp_snapshot/20161220/1.11.2/srgs/srg-mcp.srg");
    static final File       SRG_MCP_SRG   = new File(MINECRAFT_CACHE_DIR + "de/oceanlabs/mcp/mcp_snapshot/20161220/1.11.2/srgs/mcp-srg.srg");
    static final File       SRG_MCP_NOTCH = new File(MINECRAFT_CACHE_DIR + "de/oceanlabs/mcp/mcp_snapshot/20161220/1.11.2/srgs/mcp-notch.srg");
    static final File       CSV_DIR       = new File(MINECRAFT_CACHE_DIR + "de/oceanlabs/mcp/mcp_snapshot/20161220");

    protected abstract void setDefaultArguments(Map<String, String> argMap);

    protected abstract void preLaunch(Map<String, String> argMap, List<String> extras);

    protected abstract String getBounceClass();

    protected abstract String getTweakClass();

    protected void launch(String[] args) throws Throwable
    {
        // DEPRECATED, use the properties below instead!
        System.setProperty("net.minecraftforge.gradle.GradleStart.srgDir", SRG_DIR.getCanonicalPath());

        // set system vars for passwords
        System.setProperty("net.minecraftforge.gradle.GradleStart.srg.notch-srg", SRG_NOTCH_SRG.getCanonicalPath());
        System.setProperty("net.minecraftforge.gradle.GradleStart.srg.notch-mcp", SRG_NOTCH_MCP.getCanonicalPath());
        System.setProperty("net.minecraftforge.gradle.GradleStart.srg.srg-mcp", SRG_SRG_MCP.getCanonicalPath());
        System.setProperty("net.minecraftforge.gradle.GradleStart.srg.mcp-srg", SRG_MCP_SRG.getCanonicalPath());
        System.setProperty("net.minecraftforge.gradle.GradleStart.srg.mcp-notch", SRG_MCP_NOTCH.getCanonicalPath());
        System.setProperty("net.minecraftforge.gradle.GradleStart.csvDir", CSV_DIR.getCanonicalPath());

        // set defaults!
        setDefaultArguments(argMap);

        // parse stuff
        parseArgs(args);

        // now send it back for prelaunch
        preLaunch(argMap, extras);

        // because its the dev env.
        System.setProperty("fml.ignoreInvalidMinecraftCertificates", "true"); // cant hurt. set it now.

        GradleForgeHacks.searchCoremods(this);

        // now the actual launch args.
        args = getArgs();

        // clear it out
        argMap = null;
        extras = null;

        // launch.
        System.gc();
        Class.forName(getBounceClass()).getDeclaredMethod("main", String[].class).invoke(null, new Object[] { args });
    }

    private String[] getArgs()
    {
        ArrayList<String> list = new ArrayList<String>(22);

        for (Map.Entry<String, String> e : argMap.entrySet())
        {
            String val = e.getValue();
            if (!Strings.isNullOrEmpty(val))
            {
                list.add("--" + e.getKey());
                list.add(val);
            }
        }

        // grab tweakClass
        if (!Strings.isNullOrEmpty(getTweakClass()))
        {
            list.add("--tweakClass");
            list.add(getTweakClass());
        }

        if (extras != null)
        {
            list.addAll(extras);
        }

        String[] out = list.toArray(new String[list.size()]);

        // final logging.
        StringBuilder b = new StringBuilder();
        b.append('[');
        for (int x = 0; x < out.length; x++)
        {
            b.append(out[x]);
            if ("--accessToken".equalsIgnoreCase(out[x]))
            {
                b.append("{REDACTED}");
                x++;
            }

            if (x < out.length - 1)
            {
                b.append(", ");
            }
        }
        b.append(']');
        GradleStartCommon.LOGGER.info("Running with arguments: " + b.toString());

        return out;
    }

    private void parseArgs(String[] args)
    {
        final OptionParser parser = new OptionParser();
        parser.allowsUnrecognizedOptions();

        for (String key : argMap.keySet())
        {
            parser.accepts(key).withRequiredArg().ofType(String.class);
        }

        final NonOptionArgumentSpec<String> nonOption = parser.nonOptions();

        final OptionSet options = parser.parse(args);
        for (String key : argMap.keySet())
        {
            if (options.hasArgument(key))
            {
                String value = (String) options.valueOf(key);
                argMap.put(key, value);
                if (!"password".equalsIgnoreCase(key))
                    LOGGER.info(key + ": " + value);
            }
        }

        extras = Lists.newArrayList(nonOption.values(options));
        LOGGER.info("Extra: " + extras);
    }
}
