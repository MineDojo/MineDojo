// --------------------------------------------------------------------------------------------------
//  Copyright (c) 2016 Microsoft Corporation
//
//  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
//  associated documentation files (the "Software"), to deal in the Software without restriction,
//  including without limitation the rights to use, copy, modify, merge, publish, distribute,
//  sublicense, and/or l copies of the Software, and to permit persons to whom the Software is
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

import com.microsoft.Malmo.MalmoMod;
import com.microsoft.Malmo.Client.MalmoModClient.InputType;
import com.microsoft.Malmo.MissionHandlerInterfaces.IWantToQuit;
import com.microsoft.Malmo.Schemas.MissionInit;
import com.microsoft.Malmo.Utils.LogHelper;
import com.microsoft.Malmo.Utils.TCPUtils;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.profiler.Profiler;
import com.microsoft.Malmo.Utils.TimeHelper;

import net.minecraftforge.common.config.Configuration;
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.Charset;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.Hashtable;
import com.microsoft.Malmo.Utils.TCPInputPoller;
import java.util.logging.Level;

import java.util.LinkedList;
import java.util.List;


/**
 * MalmoEnvServer - service supporting OpenAI gym "environment" for multi-agent Malmo missions.
 */
public class MalmoEnvServer implements IWantToQuit {
    private static Profiler profiler = new Profiler();
    private static int nsteps = 0;
    private static boolean debug = false;

    private static String hello = "<MalmoEnv" ;

    private class EnvState {

        // Mission parameters:
        String missionInit = null;
        String token = null;
        String experimentId = null;
        int agentCount = 0;
        int reset = 0;
        boolean quit = false;
        boolean synchronous = false;
        Long seed = null;

        // OpenAI gym state:
        boolean done = false;
        boolean running = false;
        double reward = 0.0;
        byte[] obs = null;
        String info = "{}";
        LinkedList<String> commands = new LinkedList<String>();
    }

    private static boolean envPolicy = false; // Are we configured by config policy?

    // Synchronize on EnvStateasd
    

    private Lock lock = new ReentrantLock();
    private Condition cond = lock.newCondition();

    private EnvState envState = new EnvState();
    private EnvState previousEnvState = null;

    private boolean shouldUsePreviousEnvState = false;

    private Hashtable<String, Integer> initTokens = new Hashtable<String, Integer>();

    static final long COND_WAIT_SECONDS = 3; // Max wait in seconds before timing out (and replying to RPC).
    static final int BYTES_INT = 4;
    static final int BYTES_DOUBLE = 8;
    private static final Charset utf8 = Charset.forName("UTF-8");

    // Service uses a single per-environment client connection - initiated by the remote environment.

    private int port;
    private TCPInputPoller missionPoller; // Used for command parsing and not actual communication.
    private String version;
    private MalmoModClient inputController;

    /***
     * Malmo "Env" service.
     * @param port the port the service listens on.
     * @param missionPoller for plugging into existing comms handling.
     */
    public MalmoEnvServer(String version, int port, TCPInputPoller missionPoller, MalmoModClient inputController) {
        this.version = version;
        this.missionPoller = missionPoller;
        this.port = port;
        this.inputController = inputController;
    }

    /** Initialize malmo env configuration. For now either on or "legacy" AgentHost protocol.*/
    static public void update(Configuration configs) {
        envPolicy = configs.get(MalmoMod.ENV_CONFIGS, "env", "false").getBoolean();
    }

    public static boolean isEnv() {
        return envPolicy;
    }

    /**
     * Start servicing the MalmoEnv protocol.
     * @throws IOException
     */
    public void serve() throws IOException {
        ServerSocket serverSocket = new ServerSocket(port);
        serverSocket.setPerformancePreferences(0,2,1);

        while (true) {
            try {
                final Socket socket = serverSocket.accept();
                socket.setTcpNoDelay(true);
                Thread thread = new Thread("EnvServerSocketHandler") {
                    public void run() {
                        boolean running = false;
                        try {
                            checkHello(socket);

                            while (true) {
                                
                                DataInputStream din = new DataInputStream(socket.getInputStream());
                                int hdr = 0;
                                try {
                                    hdr = din.readInt();
                                } catch (EOFException e) {
                                    LogHelper.debug("Incoming socket connection closed, likely by peer (without Exit message): " + e);
                                    socket.close();
                                    break;
                                }
                                byte[] data = new byte[hdr];
                                
                                din.readFully(data);
                                

                                String command = new String(data, utf8);

                                if (command.startsWith("<StepClient")) {

                                    stepClient(command, socket, din);

                                } else if (command.startsWith("<StepServer")) {

                                    stepServer(command, socket);

                                } else if (command.startsWith("<Peek")) {

                                    peek(command, socket, din);

                                } else if (command.startsWith("<Init")) {

                                    init(command, socket);

                                } else if (command.startsWith("<Find")) {

                                    find(command, socket);

                                } else if (command.startsWith("<Interact")) {

                                    interact(command, socket);

                                } else if (command.startsWith("<MissionInit")) {

                                    if (missionInit(din, command, socket))
                                        {
                                            running = true;
                                        }

                                } else if (command.startsWith("<Quit")) {

                                    quit(command, socket);

                                    profiler.profilingEnabled = false;

                                } else if (command.startsWith("<Exit")) {

                                    exit(command, socket);

                                    profiler.profilingEnabled = false;

                                    return; // exit

                                } else if (command.startsWith("<Close")) {

                                    close(command, socket);
                                    profiler.profilingEnabled = false;

                                }  else if (command.startsWith("<Status")) {

                                    status(command, socket);

                                } else if (command.startsWith("<Echo")) {
                                    command = "<Echo>" + command + "</Echo>";
                                    data = command.getBytes(utf8);
                                    hdr = data.length;

                                    DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
                                    dout.writeInt(hdr);
                                    dout.write(data, 0, hdr);
                                    dout.flush();
                                } else if (command.startsWith("<Disconnect")) {
                                    socket.close();
                                    break;
                                } else {
                                    throw new IOException("Unknown env service command: " + command);
                                }
                            }
                        } catch (IOException ioe) {
                            ioe.printStackTrace();
                            TCPUtils.Log(Level.SEVERE, "MalmoEnv socket error: " + ioe + " (can be on disconnect)");
                            
                            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] MalmoEnv socket error");
                            try {
                                if (running) {
                                    TCPUtils.Log(Level.INFO,"Want to quit on disconnect.");

                                    System.out.println( "[LOGTOPY] " + "Want to quit on disconnect.");
                                    setWantToQuit();
                                }
                                socket.close();
                            } catch (IOException ioe2) {
                            }
                        } catch (Exception e) {
                            LogHelper.error("Error while processing commands", e);
                            try {
                                socket.close();
                            } catch (IOException ioe2) {
                            }
                        }
                    }
                };
                thread.start();
            } catch (IOException ioe) {
                TCPUtils.Log(Level.SEVERE, "MalmoEnv service exits on " + ioe);
                LogHelper.error("IO Error while processing commands", ioe);
            } catch (Exception e) {
                LogHelper.error("Error while processing commands", e);
            }
        }
    }

    private void checkHello(Socket socket) throws IOException {
        
        DataInputStream din = new DataInputStream(socket.getInputStream());
        int hdr = din.readInt();
        if (hdr <= 0 || hdr > hello.length() + 8) // Version number may be somewhat longer in future.
            throw new IOException("Invalid MalmoEnv hello header length");
        byte[] data = new byte[hdr];
        din.readFully(data);
        if (!new String(data).startsWith(hello + version))
            throw new IOException("MalmoEnv invalid protocol or version - expected " + hello + version);
        
    }

    // Handler for <MissionInit> messages.
    private boolean missionInit(DataInputStream din, String command, Socket socket) throws IOException {
        String ipOriginator = socket.getInetAddress().getHostName();

        int hdr;
        byte[] data;
        hdr = din.readInt();
        data = new byte[hdr];
        din.readFully(data);
        String id = new String(data, utf8);

        TCPUtils.Log(Level.INFO,"Mission Init" + id);

        String[] token = id.split(":");
        String experimentId = token[0];
        int role = Integer.parseInt(token[1]);
        int reset = Integer.parseInt(token[2]);
        int agentCount = Integer.parseInt(token[3]);
        Boolean isSynchronous = Boolean.parseBoolean(token[4]);
        Long seed = null;
        if(token.length > 5)
            seed = Long.parseLong(token[5]);

//        port = -1;  // FIXME - why was this happening?
        boolean allTokensConsumed = true;
        boolean started = false;

        lock.lock();
        try {
            TimeHelper.SyncManager.role = role;
            if (role == 0) {
                String previousToken = experimentId + ":0:" + (reset - 1);
                
                initTokens.remove(previousToken);

                String myToken = experimentId + ":0:" + reset;
                if (!initTokens.containsKey(myToken)) {
                    TCPUtils.Log(Level.INFO,"(Pre)Start " + role + " reset " + reset);
                    started = startUp(command, ipOriginator, experimentId, reset, agentCount, myToken, seed, isSynchronous);
                    if (started)
                        initTokens.put(myToken, 0);
                } else {
                    started = true; // Pre-started previously.
                }

                // Check that all previous tokens have been consumed. If not don't proceed to mission.

                allTokensConsumed = areAllTokensConsumed(experimentId, reset, agentCount);
                if (!allTokensConsumed) {
                    try {
                        cond.await(COND_WAIT_SECONDS, TimeUnit.SECONDS);
                    } catch (InterruptedException ie) {
                    }
                    allTokensConsumed = areAllTokensConsumed(experimentId, reset, agentCount);
                }
            } else {
                TCPUtils.Log(Level.INFO, "Start " + role + " reset " + reset);

                started = startUp(command, ipOriginator, experimentId, reset, agentCount, experimentId + ":" + role + ":" + reset, seed, isSynchronous);
            }
        } finally {
            lock.unlock();
        }

        
        DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
        dout.writeInt(BYTES_INT);
        dout.writeInt(allTokensConsumed && started ? 1 : 0);
        dout.flush();

        dout.flush();

        return allTokensConsumed && started;
    }

    private boolean areAllTokensConsumed(String experimentId, int reset, int agentCount) {
        boolean allTokensConsumed = true;
        for (int i = 1; i < agentCount; i++) {
            String tokenForAgent = experimentId + ":" + i + ":" + (reset - 1);
            if (initTokens.containsKey(tokenForAgent)) {
                TCPUtils.Log(Level.FINE,"Mission init - unconsumed " + tokenForAgent);
                allTokensConsumed = false;
            }
        }
        return allTokensConsumed;
    }

    private boolean startUp(String command, String ipOriginator, String experimentId, int reset, int agentCount, String myToken, Long seed, Boolean isSynchronous) throws IOException {

        // Clear out mission state
        envState.reward = 0.0;
        envState.commands.clear();
        envState.obs = null;
        envState.info = "{}";


        envState.missionInit = command;
        envState.done = false;
        envState.running = true;
        envState.quit = false;
        envState.token = myToken;
        envState.experimentId = experimentId;
        envState.agentCount = agentCount;
        envState.reset = reset;
        envState.synchronous = isSynchronous;
        envState.seed = seed;
        
        return startUpMission(command, ipOriginator);
    }

    private boolean startUpMission(String command, String ipOriginator) throws IOException {

        if (missionPoller == null)
            return false;

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DataOutputStream dos = new DataOutputStream(baos);

        missionPoller.commandReceived(command, ipOriginator, dos);
        

        dos.flush();
        byte[] reply = baos.toByteArray();
        ByteArrayInputStream bais = new ByteArrayInputStream(reply);
        DataInputStream dis = new DataInputStream(bais);
        int hdr = dis.readInt();
        byte[] replyBytes = new byte[hdr];
        dis.readFully(replyBytes);

        String replyStr = new String(replyBytes);
        
        if (replyStr.equals("MALMOOK")) {
            TCPUtils.Log(Level.INFO, "MalmoEnvServer Mission starting ...");
            return true;
        } else if (replyStr.equals("MALMOBUSY")) {
            TCPUtils.Log(Level.INFO, "MalmoEnvServer Busy - I want to quit");
            this.envState.quit = true;
        }
        return false;
    }

    private void waitTick() {
        // run a client tick
        
        TimeHelper.SyncManager.clientTick.requestAndWait();
        // run a server tick
        if (TimeHelper.SyncManager.role == 0) 
            TimeHelper.SyncManager.serverTick.requestAndWait();

    }

    private static final int stepClientTagLength = "<StepClient_>".length(); // Step with option code.
    private synchronized void stepClientSync(String command, Socket socket, DataInputStream din) throws IOException
    {
        profiler.startSection("rootClient");
        // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <StepClient_> Entering synchronous step.");

        profiler.startSection("commandProcessing");
        String actions = command.substring(stepClientTagLength, command.length() - (stepClientTagLength + 2));
        nsteps += 1;
        int options =  Character.getNumericValue(command.charAt(stepServerTagLength - 2));
        boolean withInfo = options == 0 || options == 2;

        // Prepare to write data to the client.
        DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
        double reward = 0.0;
        boolean done;
        byte[] obs;
        String info = "";
        boolean sent = true;

        // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Acquiring lock for synchronous step.");

        lock.lock();
        try {
            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Lock is acquired.");

            done = envState.done;
            // TODO Handle when the environment is done.

            // Process the actions.
            if (actions.contains("\n")) {
                String[] cmds = actions.split("\\n");
                for (String cmd : cmds) {
                    envState.commands.add(cmd);
                }
            } else {
                if (!actions.isEmpty())
                    envState.commands.add(actions);
            }
            sent = true;

            profiler.endSection(); //cmd
            profiler.startSection("clientTick");

//            TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Received: " + actions);
//            TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Requesting tick. Should use previous env state: " + Boolean.toString(shouldUsePreviousEnvState));
            // Now wait to run a tick

            // If synchronous mode is off then we should see if want to quit is true.
            if(!done) 
                TimeHelper.SyncManager.clientTick.requestAndWait();

            if (shouldUsePreviousEnvState && previousEnvState != null) {
                envState = previousEnvState;
                envState.done = true;
            }
            shouldUsePreviousEnvState = false;

            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> TICK DONE.  Getting observation.");
            profiler.endSection();
            profiler.startSection("getObservation");
            // After which, get the observations.
            obs = getObservation(done);

            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Observation received. Getting info.");

            profiler.endSection();
            profiler.startSection("getInfo");

            // Pick up rewards.
            reward = envState.reward;
            if (withInfo) {
                info = envState.info;
                // when none info, ideally, we should wait for new info as in the commented code.
                // But don't know why it's very slow to get new info
                // So we just use previous info in this case. Info will still update, at a lower speed....
                if (info == "{}") {
                    info = previousEnvState.info;
                    envState.info = previousEnvState.info;
                }
//                if (info == "{}" && !done) {
//                    try {
//                        cond.await(COND_WAIT_SECONDS, TimeUnit.SECONDS);
//                    } catch (InterruptedException ie) {
//                    }
//                    info = envState.info;
//                }

            }
            done = envState.done;

            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> STATUS " + Boolean.toString(done));

            // if done, desynchronize the environment!
            if (done) {
                TimeHelper.SyncManager.setSynchronous(false);
            }

            previousEnvState = new EnvState();
            previousEnvState.reward = envState.reward;
            previousEnvState.commands = envState.commands;
            previousEnvState.obs = envState.obs;
            previousEnvState.info = envState.info;
            previousEnvState.missionInit = envState.missionInit;
            previousEnvState.done = envState.done;
            previousEnvState.running = envState.running;
            previousEnvState.quit = envState.quit;
            previousEnvState.token = envState.token;
            previousEnvState.experimentId = envState.experimentId;
            previousEnvState.agentCount = envState.agentCount;
            previousEnvState.reset = envState.reset;
            previousEnvState.synchronous = envState.synchronous;
            previousEnvState.seed = envState.seed;


            envState.info = "{}";
            envState.obs = null;
            envState.reward = 0.0;

            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Info received..");
            profiler.endSection();
        } finally {
            lock.unlock();
        }

        // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Lock released. Writing observation, info, done.");

        profiler.startSection("writeObs");
        dout.writeInt(obs.length);
        dout.write(obs);

        dout.writeInt(BYTES_DOUBLE + 2);
        dout.writeDouble(reward);
        dout.writeByte(done ? 1 : 0);
        dout.writeByte(sent ? 1 : 0);

        if (withInfo) {
            byte[] infoBytes = info.getBytes(utf8);
            dout.writeInt(infoBytes.length);
            dout.write(infoBytes);
        }

        profiler.endSection(); //write obs
        profiler.startSection("flush");

        // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Packets written. Flushing.");
        dout.flush();
        profiler.endSection(); // flush

        profiler.endSection(); // rootClient
    }

    private static final int stepServerTagLength = "<StepServer_>".length(); // Step with option code.
    private synchronized void stepServerSync(String command, Socket socket) throws IOException
    {
        profiler.startSection("rootServer");
        // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <StepServer_> Entering synchronous step.");

        // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Acquiring lock for synchronous step.");

        lock.lock();
        try {
            // Then wait until the tick is finished
            boolean done = envState.done;

            profiler.startSection("serverTick");
            

            if(!done) TimeHelper.SyncManager.serverTick.requestAndWait();
            else TimeHelper.SyncManager.setSynchronous(false);

            profiler.endSection();
        } finally {
            lock.unlock();
        }

        // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <STEP> Done with step.");
        profiler.endSection(); // rootServer
    }

    // Handler for <StepClient_> messages. Single digit option code after _ specifies if turnkey and info are included in message.
    private void stepClient(String command, Socket socket, DataInputStream din) throws IOException {
        if(envState.synchronous){
            stepClientSync(command, socket, din);
        }
        else{
            
        }
    }

    // Handler for <StepServer_> messages.
    private void stepServer(String command, Socket socket) throws IOException {
        if(envState.synchronous){
            long start = System.nanoTime();

            stepServerSync(command, socket);

            if (nsteps % 100 == 0 && debug){
                List<Profiler.Result> dat = profiler.getProfilingData("root");
                for(int qq = 0; qq < dat.size(); qq++){
                    Profiler.Result res = dat.get(qq);
                    System.out.println(res.profilerName + " " + res.totalUsePercentage + " "+ res.usePercentage);
                }
            }
        }
        else{
            
        }
    }

    // Handler for <Peek> messages.
    private void peek(String command, Socket socket, DataInputStream din) throws IOException {

        DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
        byte[] obs;
        boolean done;
        String info = "";

        lock.lock();

        try {
            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <PEEK> Waiting for pistol to fire.");
            while(!TimeHelper.SyncManager.hasServerFiredPistol()){
                waitTick();

                Thread.yield(); 
            }

            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <PEEK>  Pistol fired!.");
            // Wait two ticks for the first observation from server to be propagated.
            while(! TimeHelper.SyncManager.isSynchronous() ){ 
                waitTick();
                Thread.yield();
            }

            waitTick();
            waitTick();


            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <PEEK> Getting observation.");

            obs = getObservation(false);

            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <PEEK> Observation acquired.");
            done = envState.done;
            info = envState.info;
           
        } finally {
            lock.unlock();
        }

        dout.writeInt(obs.length);
        dout.write(obs);

        byte[] infoBytes = info.getBytes(utf8);
        dout.writeInt(infoBytes.length);
        dout.write(infoBytes);

        dout.writeInt(1);
        dout.writeByte(done ? 1 : 0);

        dout.flush();
    }

    // Get the current observation. If none and not done wait for a short time.
    public byte[] getObservation(boolean done)  {
        byte[] obs = envState.obs;
        if (obs == null && !done) {
            try {
                cond.await(COND_WAIT_SECONDS, TimeUnit.SECONDS);
            } catch (InterruptedException ie) {
            }
            obs = envState.obs;
        }
        return obs;
    }

    // Handler for <Find> messages - used by non-zero roles to discover integrated server port from primary (role 0) service.

    private final static int findTagLength = "<Find>".length();

    private void find(String command, Socket socket) throws IOException {

        Integer port;
        lock.lock();
        try {
            String token = command.substring(findTagLength, command.length() - (findTagLength + 1));
            TCPUtils.Log(Level.INFO, "Find token? " + token);

            // Purge previous token.
            String[] tokenSplits = token.split(":");
            String experimentId = tokenSplits[0];
            int role = Integer.parseInt(tokenSplits[1]);
            int reset = Integer.parseInt(tokenSplits[2]);

            String previousToken = experimentId + ":" + role + ":" + (reset - 1);
            initTokens.remove(previousToken);
            cond.signalAll();

            // Check for next token. Wait for a short time if not already produced.
            port = initTokens.get(token);
            if (port == null) {
                try {
                    cond.await(COND_WAIT_SECONDS, TimeUnit.SECONDS);
                } catch (InterruptedException ie) {
                }
                port = initTokens.get(token);
                if (port == null) {
                    port = 0;
                    TCPUtils.Log(Level.INFO,"Role " + role + " reset " + reset + " waiting for token.");
                }
            }
        } finally {
            lock.unlock();
        }

        DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
        dout.writeInt(BYTES_INT);
        dout.writeInt(port);
        dout.flush();
    }

    // Handler for interact (which connects a client to an IP via multiplayer.).

    private final static int interactTagLength = "<Interact>".length();

    private void interact(String command, Socket socket) throws IOException {

        lock.lock();
        try {
            String token = command.substring(interactTagLength, command.length() - (interactTagLength + 1));
            TCPUtils.Log(Level.INFO, "Find token? " + token);

            // Purge previous token.
            String[] tokenSplits = token.split(":");
            String ip = tokenSplits[0];
            String port = tokenSplits[1];
            //Print the ip and port
            final ServerData sd = new ServerData("agent server", ip + ":" + port, false);
            net.minecraftforge.fml.client.FMLClientHandler.instance().getClient().addScheduledTask(new Runnable() {
                public void run() {
                    GuiScreen old_gui = net.minecraftforge.fml.client.FMLClientHandler.instance().getClient().currentScreen;
                    net.minecraftforge.fml.client.FMLClientHandler.instance().setupServerList();
                    net.minecraftforge.fml.client.FMLClientHandler.instance().connectToServer(old_gui, sd);
                }
            });
            
            // Bad menu behaviour
            // this.inputController.setInputType(InputType.HUMAN);
            Minecraft.getMinecraft().mouseHelper = this.inputController.originalMouseHelper;
            System.setProperty("fml.noGrab", "false");
            // Minecraft.getMinecraft().mouseHelper.grabMouseCursor();
           

        } finally {
            lock.unlock();
        }
        // Say that we r done.
        DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
        dout.writeInt(BYTES_INT);
        dout.writeInt(1);
        dout.flush();
    }

    public boolean isSynchronous(){
        return envState.synchronous;
    }

    // Handler for <Init> messages. These reset the service so use with care!
    private void init(String command, Socket socket) throws IOException {
        lock.lock();
        try {
            initTokens = new Hashtable<String, Integer>();
            DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
            dout.writeInt(BYTES_INT);
            dout.writeInt(1);
            dout.flush();
        } finally {
            lock.unlock();
        }
    }

    // Handler for <Quit> (quit mission) messages.
    private void quit(String command, Socket socket) throws IOException {
        lock.lock();
        try {
            if (!envState.done){
                
                envState.quit = true;
            }

            waitTick();
            waitTick();
            TimeHelper.SyncManager.setSynchronous(false);

            DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
            dout.writeInt(BYTES_INT);
            dout.writeInt((envState.done || !envState.running) ? 1 : 0);
            dout.flush();
        } finally {
            lock.unlock();
        }
    }

    private final static int closeTagLength = "<Close>".length();

    // Handler for <Close> messages.
    private void close(String command, Socket socket) throws IOException {
        lock.lock();
        try {
            String token = command.substring(closeTagLength, command.length() - (closeTagLength + 1));

            initTokens.remove(token);

            DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
            dout.writeInt(BYTES_INT);
            dout.writeInt(1);
            dout.flush();
        } finally {
            lock.unlock();
        }
    }

    // Handler for <Status> messages.
    private void status(String command, Socket socket) throws IOException {
        lock.lock();
        try {
            String status = "{}"; // TODO Possibly have something more interesting to report.
            DataOutputStream dout = new DataOutputStream(socket.getOutputStream());

            byte[] statusBytes = status.getBytes(utf8);
            dout.writeInt(statusBytes.length);
            dout.write(statusBytes);

            dout.flush();
        } finally {
            lock.unlock();
        }
    }

    // Handler for <Exit> messages. These "kill the service" temporarily so use with care!f
    private void exit(String command, Socket socket) throws IOException {
        // lock.lock();
        try {
             // We may exit before we get a chance to reply.
            TimeHelper.SyncManager.setSynchronous(false);
            DataOutputStream dout = new DataOutputStream(socket.getOutputStream());
            dout.writeInt(BYTES_INT);
            dout.writeInt(1);
            dout.flush();

            ClientStateMachine.exitJava();

        } finally {
            // lock.unlock();
        }
    }

    // Malmo client state machine interface methods:

    public String getCommand() {
        try {
            String command = envState.commands.poll();
            if (command == null)
                return "";
            else
                return command;
        } finally {
        }
    }

    public void endMission() {
        // lock.lock();
        try {
            envState.done = true;
            envState.quit = false;
            envState.missionInit = null;

            if (envState.token != null) {
                initTokens.remove(envState.token);
                envState.token = null;
                envState.experimentId = null;
                envState.agentCount = 0;
                envState.reset = 0;

                // cond.signalAll();
            }
            // lock.unlock();
        } finally {
        }
    }

    public void setRunning(boolean running) {
        envState.running = false;
    }

    public void usePreviousState() {
        shouldUsePreviousEnvState = true;
    }

    // Record a Malmo "observation" json - as the env info since an environment "obs" is a video frame.
    public void observation(String info) {
        // Parsing obs as JSON would be slower but less fragile than extracting the turn_key using string search.
        // lock.lock();
        try {
            // TimeHelper.SyncManager.debugLog("[MALMO_ENV_SERVER] <OBSERVATION> Inserting: " + info);
            envState.info = info;
            // cond.signalAll();
        } finally {
            // lock.unlock();
        }
    }

    public void addRewards(double rewards) {
        // lock.lock();
        try {
            envState.reward += rewards;
        } finally {
            // lock.unlock();
        }
    }

    public void addFrame(byte[] frame) {
        // lock.lock();
        try {
            envState.obs = frame; // Replaces current.
            // System.out.println("[ERROR] ADD FRAME, " + (frame == null) + ", sync " + TimeHelper.SyncManager.isSynchronous() );
            // cond.signalAll();
        } finally {
            // lock.unlock();
        }
    }

    public void notifyIntegrationServerStarted(int integrationServerPort) {
         lock.lock();
        try {
            if (envState.token != null) {
                TCPUtils.Log(Level.INFO,"Integration server start up - token: " + envState.token);
                addTokens(integrationServerPort, envState.token, envState.experimentId, envState.agentCount, envState.reset);
                cond.signalAll();
            } else {
                TCPUtils.Log(Level.WARNING,"No mission token on integration server start up!");
            }
        } finally {
             lock.unlock();
        }
    }

    private void addTokens(int integratedServerPort, String myToken, String experimentId, int agentCount, int reset) {
        initTokens.put(myToken, integratedServerPort);
        // Place tokens for other agents to find.
        for (int i = 1; i < agentCount; i++) {
            String tokenForAgent = experimentId + ":" + i + ":" + reset;
            initTokens.put(tokenForAgent, integratedServerPort);
        }
    }

    // IWantToQuit implementation.

    @Override
    public boolean doIWantToQuit(MissionInit missionInit) {
        // lock.lock();
        try {
           return envState.quit;
        } finally {
            // lock.unlock();
        }
    }

    public Long getSeed(){
        return envState.seed;
    }

    private void setWantToQuit() {
        // lock.lock();
        try {
            envState.quit = true;
            
        } finally {

            if(TimeHelper.SyncManager.isSynchronous()){
                // We want to dsynchronize everything.
                TimeHelper.SyncManager.setSynchronous(false);
            }
            // lock.unlock();
        }
    }

    @Override
    public void prepare(MissionInit missionInit) {
    }

    @Override
    public void cleanup() {
    }

    @Override
    public String getOutcome() {
        return "Env quit";
    }
}
