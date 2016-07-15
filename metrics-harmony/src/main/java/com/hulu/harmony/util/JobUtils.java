package com.hulu.harmony.util;

import com.hulu.harmony.api.configuration.ConfigurationKeys;
import com.hulu.harmony.api.configuration.State;

/**
 * Job utils class
 *
 * @author tamirw
 */
public class JobUtils {

    /**
     * Get phase name
     *
     * @param stackLevel thread stack level
     */
    public static String getPhaseName(int stackLevel) {
        return Thread.currentThread().getStackTrace()[stackLevel].getMethodName();
    }

    /**
     * Set state end properties
     *
     * @param state state configuration and runtime data
     * @param phaseName phase name
     * @param key property key
     */
    public static void setStateEndProperties(State state, String phaseName, String key) {
        state.setRunningStateEndTime(phaseName, System.currentTimeMillis());
        state.setProp(key, ConfigurationKeys.JOB_STATE_FINISH_STATUS);
    }
}
